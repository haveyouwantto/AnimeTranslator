import subprocess
import tempfile
from pathlib import Path
import pysubs2
from .base import ASSource
from models.subtitle import Subtitle, SubtitleSegment
from typing import Optional

import re

class ASSEmbeddedSource(ASSource):
    """内嵌ASS字幕提取器（专门提取英文字幕）"""
    
    def __init__(self):
        super().__init__()
        self.languages = ['en', 'eng']  # 支持的英语语言代码
    
    def _detect_subtitle_language(self, video_path: str) -> str:
        """检测字幕流语言"""
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-hide_banner'
        ]
        result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)
        
        for line in result.stderr.split('\n'):
            if 'Stream #' in line and 'Subtitle' in line:
                for lang in self.languages:
                    if lang in line.lower():
                        match = re.search(r"#(\d+:\d+)", line.lower())

                        if match:
                            result = match.group(1)
                            return result
        return None
    
    def get_subtitle(self, video_path: str) -> Optional[Subtitle]:
        """提取视频中的英文字幕流"""
        stream_index = self._detect_subtitle_language(video_path)
        if not stream_index:
            return None
            
        try:
            with tempfile.NamedTemporaryFile(suffix='.ass', delete=False) as tmp:
                cmd = [
                    'ffmpeg',
                    '-loglevel', 'error',
                    '-i', str(video_path),
                    '-map', f'{stream_index}',  # 提取指定字幕流
                    '-c:s', 'ass',
                    '-y', tmp.name
                ]
                subprocess.call(cmd)
                
                self.original_ass = pysubs2.load(tmp.name)
                segments = [
                    SubtitleSegment(
                        line_number=i+1,
                        start=event.start / 1000,  # 毫秒转秒
                        end=event.end / 1000,
                        text=event.text,
                        character=event.name if len(event.name) > 0 else "default"
                    )
                    for i, event in enumerate(self.original_ass.events)
                    if event.type == "Dialogue"
                ]
                Path(tmp.name).unlink()
                return Subtitle(segments)
        except Exception as e:
            raise e

