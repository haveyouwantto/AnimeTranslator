import subprocess
import tempfile
import os
from typing import Optional
from models.subtitle import Subtitle, SubtitleSegment
from .base_source import BaseSubtitleSource
from utils.time_utils import srt_time_to_seconds

class EmbeddedSource(BaseSubtitleSource):
    def get_subtitle(self, audio_path: str) -> Subtitle:
        """提取视频文件中的内嵌英文字幕"""
        temp_srt = self._extract_embedded_subtitles(audio_path)
        if temp_srt:
            try:
                return self._parse_srt(temp_srt)
            finally:
                os.remove(temp_srt)
        raise Exception("No embedded English subtitles found")

    def _extract_embedded_subtitles(self, file_path: str) -> Optional[str]:
        """使用ffmpeg提取内嵌字幕到临时文件"""
        try:
            # 检测是否有英文字幕流
            cmd = ['ffmpeg', '-i', file_path, '-hide_banner']
            result = str(subprocess.run(cmd, stderr=subprocess.PIPE).stderr, encoding='utf-8')
            
            if 'Stream #' in result and 'Subtitle' in result:
                # 查找英文字幕流
                streams = [line for line in result.split('\n') 
                         if 'Stream #' in line and 'Subtitle' in line and ('eng' in line or 'en' in line)]
                
                if streams:
                    # 创建临时文件
                    fd, temp_path = tempfile.mkstemp(suffix='.srt')
                    os.close(fd)
                    
                    # 提取第一个英文字幕流
                    extract_cmd = [
                        'ffmpeg',
                        '-i', file_path,
                        '-map', '0:s:m:language:eng',  # 提取所有英文字幕流
                        '-c:s', 'srt',
                        '-loglevel', 'error',
                        '-y',
                        temp_path
                    ]
                    subprocess.run(extract_cmd, check=True)
                    return temp_path
        except Exception as e:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
            raise Exception(f"Failed to extract embedded subtitles: {str(e)}")
        return None

    def _parse_srt(self, srt_path: str) -> Subtitle:
        """解析SRT文件为Subtitle对象"""
        segments = []
        current_segment = None
        lineno = 1
        
        with open(srt_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                if not line:
                    if current_segment and current_segment.text:
                        segments.append(current_segment)
                        current_segment = None
                    continue
                    
                if ' --> ' in line:
                    start_str, end_str = line.split(' --> ')
                    current_segment = SubtitleSegment(
                        start=srt_time_to_seconds(start_str),
                        end=srt_time_to_seconds(end_str),
                        text='',
                        line_number=lineno
                    )
                    lineno+=1
                elif current_segment and not line.isdigit():
                    current_segment.text += (' ' + line) if current_segment.text else line
        
        if current_segment and current_segment.text:
            segments.append(current_segment)
            
        return Subtitle(segments)