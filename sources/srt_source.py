import os
from models.subtitle import Subtitle, SubtitleSegment
from .base_source import BaseSubtitleSource
from utils.time_utils import srt_time_to_seconds

class SRTSource(BaseSubtitleSource):
    def get_subtitle(self, audio_path: str) -> Subtitle:
        base_path = os.path.splitext(audio_path)[0]
        possible_paths = [
            f"{base_path}.en.srt",
            f"{base_path}.srt",
            f"{audio_path}.en.srt"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return self._parse_srt(path)
        raise FileNotFoundError("No SRT file found")
    
    def _parse_srt(self, srt_path: str) -> Subtitle:
        segments = []
        current_segment = None
        line_counter = 1  # SRT文件的行号从1开始
        
        with open(srt_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                if not line:
                    if current_segment and current_segment.text:
                        current_segment.line_number = line_counter
                        segments.append(current_segment)
                        line_counter += 1
                        current_segment = None
                    continue
                    
                if ' --> ' in line:
                    start_str, end_str = line.split(' --> ')
                    current_segment = SubtitleSegment(
                        start=srt_time_to_seconds(start_str),
                        end=srt_time_to_seconds(end_str),
                        text='',
                        line_number=0  # 临时值，后面会设置
                    )
                elif current_segment and not line.isdigit():
                    current_segment.text += (' ' + line) if current_segment.text else line
        
        if current_segment and current_segment.text:
            current_segment.line_number = line_counter
            segments.append(current_segment)
        
        return Subtitle(segments)