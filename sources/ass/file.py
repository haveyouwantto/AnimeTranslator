from pathlib import Path
import pysubs2
from .base import ASSource
from models.subtitle import Subtitle, SubtitleSegment

class ASSFileSource(ASSource):
    """外挂ASS/SSA文件源（优先英语）"""
    
    def find_ass_files(self, video_path: Path) -> list[Path]:
        """查找所有可能的ASS文件（优先英语）"""
        base_stem = video_path.stem
        candidates = [
            # 优先英语字幕
            video_path.with_name(f"{base_stem}.en.ass"),
            video_path.with_name(f"{base_stem}.eng.ass"),
            # 通用匹配
            video_path.with_suffix('.ass'),
            video_path.with_suffix('.ssa'),
            video_path.with_name(f"{base_stem}.ja.ass")
        ]
        return [p for p in candidates if p.exists()]
    
    def get_subtitle(self, video_path: str) -> Subtitle:
        video_path = Path(video_path)
        for ass_path in self.find_ass_files(video_path):
            try:
                self.original_ass = pysubs2.load(str(ass_path))
                self.ass_path = ass_path
                
                segments = [
                    SubtitleSegment(
                        line_number=i+1,
                        start=event.start / 1000,  # 毫秒转秒
                        end=event.end / 1000,
                        text=event.text,
                        character=event.name
                    )
                    for i, event in enumerate(self.original_ass.events)
                    if event.type == "Dialogue"
                ]
                return Subtitle(segments)
            except Exception:
                continue
        return None