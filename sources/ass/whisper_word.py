from models.subtitle import Subtitle, SubtitleSegment
from .base import ASSource
import pysubs2
import logging

logger = logging.getLogger(__name__)

class WhisperWord(ASSource):
    def __init__(self, model_size: str, language: str, beam_size: int = 5):
        self.model_size = model_size
        self.language = language
        self.beam_size = beam_size

    def _load_model(self):
        from faster_whisper import WhisperModel
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        compute_type = 'float16' if torch.cuda.is_available() else 'float32'
        self.model = WhisperModel(self.model_size, device, compute_type=compute_type)

    def get_subtitle(self, video_path):
        self._load_model()
        self.original_ass = pysubs2.SSAFile()
        # 添加一个样式
        style = pysubs2.SSAStyle()
        style.name = "Default"
        style.fontname = "Arial"
        style.fontsize = 16
        style.primarycolor = pysubs2.Color(255, 255, 255, 0)      
        style.secondarycolor = pysubs2.Color(255, 255, 255, 0) 
        style.outline = 0.8
        style.shadow = 0
        style.bold = False
        style.italic = False
        style.marginv = 24
        style.alignment = pysubs2.Alignment.BOTTOM_CENTER
        self.original_ass.styles[style.name] = style

        small_style = pysubs2.SSAStyle()
        small_style.name = "Karaoke-Small"
        small_style.fontsize = 10
        small_style.primarycolor = pysubs2.Color(230, 40, 150, 0)      
        small_style.secondarycolor = pysubs2.Color(255, 255, 255, 0) 
        small_style.outline = 0.8
        small_style.shadow = 0
        small_style.bold = False
        small_style.italic = False
        small_style.marginv = 265
        small_style.alignment = pysubs2.Alignment.TOP_CENTER
        self.original_ass.styles[small_style.name] = small_style

        if self.language == 'auto':
            segments, _ = self.model.transcribe(
                video_path,
                beam_size=self.beam_size,
                word_timestamps=True
            )
        else:
            segments, _ = self.model.transcribe(
                video_path,
                language=self.language,
                beam_size=self.beam_size,
                word_timestamps=True
            )

        subtitle_segments = []
        self.original_sub = []


        for i, segment in enumerate(segments):
            text = []
            lastend = segment.start
            for word in segment.words:
                end = word.end
                delta = end - lastend
                # text.append("{\\t(%d,%d,\\c&H009628E6)}%s"%(
                #     (word.start-segment.start)*1000,
                #     (word.end-segment.start)*1000,
                #     word.word
                # ))
                text.append("{\kf"+str(int(delta*100))+"}"+word.word)
                lastend = end

            line = "".join(text)
            subtitle_segments.append(SubtitleSegment(
                start=segment.start,
                end=segment.end,
                text=segment.text,
                line_number=i+1,  # Whisper生成的行号从1开始
                character="Transcription"
            ))
            event = pysubs2.SSAEvent(
                start=segment.start*1000, 
                end=segment.end*1000, text=segment.text, style="Default")
            event2 = pysubs2.SSAEvent(
                start=segment.start*1000, 
                end=segment.end*1000, text=line, style="Karaoke-Small")
            self.original_ass.events.append(event)
            self.original_sub.append(event2)
            if i % 10 == 0:
                logger.info(f'Transcribe at {segment.start}, content: {segment.text}')
        self.original_ass.save(video_path+".original."+self.language+".ass")
        return Subtitle(subtitle_segments)
    
    def post_processing(self):
        self.original_ass.extend(self.original_sub)