from tqdm import tqdm
import sys
import json
from time import sleep
import traceback
import openai
import os


class CompactFloatEncoder(json.JSONEncoder):
    """自动四舍五入所有浮点数到两位小数"""
    def iterencode(self, o, _one_shot=False):
        # 递归处理嵌套结构
        def round_floats(obj):
            if isinstance(obj, float):
                return round(obj, 2)
            elif isinstance(obj, dict):
                return {k: round_floats(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [round_floats(e) for e in obj]
            return obj

        return super().iterencode(round_floats(o), _one_shot)

class SubtitleTranslator:
    """
    A class for transcribing audio, translating subtitles, and generating SRT files.
    """

    def __init__(self, config_path='config.yml'):
        """
        Initializes the SubtitleTranslator with configuration from a YAML file.

        Args:
            config_path (str): Path to the YAML configuration file.
        """
        self.config = self._load_config(config_path)
        openai.api_key = self.config['openai']['api_key']
        openai.api_base = self.config['openai']['api_base']

    def _load_config(self, config_path):
        """Loads configuration from a YAML file."""
        import yaml  # Move import inside the method
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_whisper_model(self):
        """Loads the Faster Whisper model."""
        import torch  # Move import inside the method
        from faster_whisper import WhisperModel  # Move import inside the method
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        compute_type = 'float32'
        return WhisperModel(self.config['whisper']['model_size'], device, compute_type=compute_type)
    
    def _convert_to_ctml(self, segments):
        """将JSON数组转换为CTML格式"""
        lines = []
        for seg in segments:
            # 时间轴处理
            start = round(seg['start'], 2)
            end = round(seg['end'], 2)
            # 转义特殊字符
            text = seg['text'].replace(':', '\:').replace('>', '\>').replace('\n', '\\n')
            lines.append(f"{start:.2f}>{end:.2f}:{text}")
        return '\n'.join(lines)

    def _parse_ctml(self, ctml_str):
        """解析CTML响应为结构化数据"""
        entries = []
        for line in ctml_str.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # 拆分时间和文本
            time_part, text = line.split(':', 1)
            
            # 解析时间轴
            start_str, end_str = time_part.split('>', 1)
            start = round(float(start_str), 2)
            end = round(float(end_str), 2)
            
            # 反转义处理
            text = text.replace('\:', ':').replace('\>', '>').replace('\\n', '\n')
            
            entries.append({
                "start": start,
                "end": end,
                "text": text
            })
        return entries

    def transcribe_audio(self, audio_path):
        """
        Transcribes the audio file into text segments.

        Args:
            audio_path (str): Path to the audio file.

        Returns:
            list: A list of dictionaries, each containing 'start', 'end', and 'text' keys.
        """
        print("Transcribing audio...")
        whisper_model = self._load_whisper_model()
        segments, info = whisper_model.transcribe(
            audio_path,
            beam_size=self.config['whisper']['beam_size'],
            language=self.config['whisper']['language'],
            condition_on_previous_text=self.config['whisper']['condition_on_previous_text'],
            word_timestamps=True
        )
        transcribed = []
        for segment in segments:
            print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
            transcribed.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
        print("Transcription complete.")
        return transcribed

    def translate_batch(self, batch, last_line, last_translation):
        """
        Translates a batch of text segments using the OpenAI API.

        Args:
            batch (list): A list of text segments (dictionaries).
            last_line (dict):  The last input line sent to the translation API
            last_translation (dict):  The last response received from the translation API

        Returns:
            list: A list of translated text segments (dictionaries), or None on failure.
        """
        import openai  # Move import inside the method
        prompt = self.config['translation']['prompt']
        retries = 0
        while retries < self.config['translation']['max_retries']:
            try:
                line = {"role": "user", "content": self._convert_to_ctml(batch)}
                response = openai.ChatCompletion.create(
                    model=self.config['openai']['model'],
                    messages=[ 
                        {"role": "system", "content": prompt},
                        last_line, last_translation, line
                    ],
                    temperature=self.config['openai']['temperature']
                )
                content = response["choices"][0]["message"]["content"].replace('```json', '').replace('```', '').strip()
                print(content)
                data = self._parse_ctml(response["choices"][0]["message"]["content"])
                return data, line, response["choices"][0]["message"]  # Return new last_line and last_translation
            except Exception as e:
                traceback.print_exc()
                sleep(self.config['translation']['retry_delay'])
                retries += 1
                continue
        print("Translation failed after multiple retries.")
        return None, last_line, last_translation

    def translate_subtitles(self, transcribed):
        """
        Translates the transcribed subtitles.

        Args:
            transcribed (list): A list of transcribed text segments.

        Returns:
            list: A list of translated text segments.
        """
        print("Translating subtitles...")
        translated = []
        last_line = {"role": "user", "content": self.config['translation']['example_input']}
        last_translation = {"role": "assistant", "content": self.config['translation']['example_output']}

        for i in tqdm(range(0, len(transcribed), self.config['translation']['batch_size'])):
            batch = transcribed[i:i + self.config['translation']['batch_size']]
            translation_result, last_line, last_translation = self.translate_batch(batch, last_line, last_translation)
            if translation_result:
                translated.extend(translation_result)
            sleep(self.config['translation']['request_interval'])
        return translated

    def seconds_to_srt_time(self, seconds: float) -> str:
        """Converts seconds to SRT format time string."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int(round((seconds - int(seconds)) * 1000))
        return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"

    def gen_srt_line(self, index, segment):
        """Generates an SRT subtitle line."""
        start_time_str = self.seconds_to_srt_time(segment['start'])
        end_time_str = self.seconds_to_srt_time(segment['end'])
        text = segment['text']
        index += 1
        return f"{index}\n{start_time_str} --> {end_time_str}\n{text}\n"

    def write_srt_file(self, translated, audio_path):
        """
        Writes the translated subtitles to an SRT file.

        Args:
            translated (list): A list of translated text segments.
            audio_path (str): Path to the original audio file (used for naming the SRT file).
        """
        print("Writing SRT file...")
        output_filename = audio_path + ".zh.srt"
        with open(output_filename, "w", encoding="utf-8") as f:
            for i, segment in enumerate(translated):
                f.write(self.gen_srt_line(i, segment))
        print(f"SRT file saved to {output_filename}")

    def _extract_embedded_subtitles(self, file_path):
        """提取内嵌英文字幕"""
        import subprocess  # Move import inside the method
        try:
            # 检测是否有英文字幕流
            cmd = [
                'ffmpeg', '-i', file_path, '-hide_banner'
            ]
            result = str(subprocess.run(cmd, stderr=subprocess.PIPE).stderr, encoding='utf-8')
            
            if 'Stream #' in result and 'Subtitle' in result:
                # 查找英文字幕流
                streams = [line for line in result.split('\n') 
                         if 'Stream #' in line and 'Subtitle' in line and 'eng' in line]
                
                if streams:
                    # 提取第一个英文字幕
                    temp_srt = f"{file_path}.temp.srt"
                    extract_cmd = [
                        'ffmpeg', '-i', file_path,
                        '-map', '0:s:m:language:eng',
                        '-c:s', 'srt',
                        '-loglevel', 'error',
                        '-y',
                        temp_srt
                    ]
                    subprocess.run(extract_cmd, check=True)
                    return temp_srt
            return None
        except Exception as e:
            traceback.print_exc()
            return None

    def _parse_srt(self, srt_path):
        """解析SRT文件为时间分段，修复多行文本处理问题"""
        segments = []
        current_segment = {}
        collecting = False  # 文本收集状态标志
        
        with open(srt_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # 空行作为段落结束标记
                if not line:
                    if current_segment.get('text'):
                        # 去除首尾空格后添加
                        current_segment['text'] = current_segment['text'].strip()
                        segments.append(current_segment)
                        current_segment = {}
                        collecting = False
                    continue
                    
                # 遇到时间码行开始新段落
                if ' --> ' in line:
                    collecting = True
                    time_parts = line.split(' --> ')
                    current_segment = {
                        'start': self._srt_time_to_seconds(time_parts[0]),
                        'end': self._srt_time_to_seconds(time_parts[1]),
                        'text': ''
                    }
                # 忽略纯数字的序号行（允许带前后空格）
                elif line.isdigit():
                    continue
                # 收集文本内容（处理多行文本）
                elif collecting:
                    current_segment['text'] += ' ' + line if current_segment['text'] else line

        # 处理文件末尾没有空行的情况
        if current_segment.get('text'):
            current_segment['text'] = current_segment['text'].strip()
            segments.append(current_segment)
            
        return segments

    def _srt_time_to_seconds(self, srt_time):
        """将SRT时间转换为秒数"""
        hours, rest = srt_time.split(':', 1)
        minutes, rest = rest.split(':', 1)
        seconds, milliseconds = rest.split(',')
        return float(hours)*3600 + float(minutes)*60 + float(seconds) + float(milliseconds)/1000

    def _check_existing_subtitles(self, audio_path):
        """检查现有字幕"""
        # 检查外挂字幕
        base_path = os.path.splitext(audio_path)[0]
        possible_paths = [
            f"{base_path}.en.srt",
            f"{base_path}.srt",
            f"{audio_path}.en.srt"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return self._parse_srt(path)
        
        # 检查内嵌字幕
        temp_srt = self._extract_embedded_subtitles(audio_path)
        if temp_srt:
            segments = self._parse_srt(temp_srt)
            os.remove(temp_srt)
            return segments
        
        return None

    def process_audio(self, audio_path):
        """
        Orchestrates the entire process: transcribing, translating, and writing the SRT file.

        Args:
            audio_path (str): Path to the audio file.
        """
        print("Starting subtitle generation process...")

        existing_sub = None
        if not self.config['common']['ignore_subtitles']:
            print("Step 1: Check existing subtitles")
            existing_sub = self._check_existing_subtitles(audio_path)
        
        transcribed = None
        if existing_sub:
            print("Using existing subtitles")
            transcribed = existing_sub
        else:
            print("No existing subtitles found")
            print("Step 2: Transcribe the audio into subtitle")
            transcribed = self.transcribe_audio(audio_path)
            print(transcribed)
        
        print("Step 3: Translate the subtitle")
        translated = self.translate_subtitles(transcribed)
        print("Step 4: Write the translated subtitle to file")
        self.write_srt_file(translated, audio_path)
        print("Subtitle generation complete.")



def main():
    """Main function to run the subtitle generation process."""
    if len(sys.argv) != 2:
        print("Usage: python your_script_name.py audio_file.mp3")
        sys.exit(1)

    audio_path = sys.argv[1]
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the config file
    config_path = os.path.join(script_dir, "config.yml")

    translator = SubtitleTranslator(config_path)
    translator.process_audio(audio_path)


if __name__ == "__main__":
    main()