from models.subtitle import SubtitleSegment
from typing import List

def convert_to_ctml(segments: List[SubtitleSegment]) -> str:
    lines = []
    for seg in segments:
        text = seg.text.replace(':', '\:').replace('>', '\>').replace('\n', '\\n')
        lines.append(f"{seg.start:.2f}>{seg.end:.2f}:{text}")
    return '\n'.join(lines)

def parse_ctml(ctml_str: str) -> List[SubtitleSegment]:
    entries = []
    for line in ctml_str.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        time_part, text = line.split(':', 1)
        start_str, end_str = time_part.split('>', 1)
        text = text.replace('\:', ':').replace('\>', '>').replace('\\n', '\n')
        
        entries.append(SubtitleSegment(
            start=float(start_str),
            end=float(end_str),
            text=text
        ))
    return entries