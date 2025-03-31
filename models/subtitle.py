from dataclasses import dataclass
from typing import List

@dataclass
class SubtitleSegment:
    start: float
    end: float
    text: str
    line_number: int = 0 

class Subtitle:
    def __init__(self, segments: List[SubtitleSegment]):
        self.segments = segments