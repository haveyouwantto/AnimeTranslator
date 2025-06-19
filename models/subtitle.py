from dataclasses import dataclass
from typing import List

@dataclass
class SubtitleSegment:
    start: float
    end: float
    text: str
    line_number: int = 0 
    character: str = "default"
    
    def __post_init__(self):
        if self.start < 0:
            self.start = 0.0
        if self.end < 0:
            self.end = 0.0
        try:
            self.line_number = int(self.line_number)
        except ValueError:
            self.line_number = 0


class Subtitle:
    def __init__(self, segments: List[SubtitleSegment]):
        self.segments = segments
