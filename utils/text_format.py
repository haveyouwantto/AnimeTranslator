from models.subtitle import SubtitleSegment

def segments_to_text(segments: list[SubtitleSegment]) -> str:
    """将字幕片段转换为纯文本格式(只包含行号和文本)"""
    return "\n".join(
        f"{seg.line_number}|{seg.text}"
        for seg in sorted(segments, key=lambda x: x.line_number)
    )

def text_to_segments(text: str, original_segments: list[SubtitleSegment]) -> list[SubtitleSegment]:
    """将翻译后的文本转换回字幕片段(保留原始行号和时间)"""
    translated = []
    line_map = {seg.line_number: seg for seg in original_segments}
    
    for line in text.split("\n"):
        line = line.strip()
        if not line or "|" not in line:
            continue
        
        line_num_str, _, content = line.partition("|")
        try:
            line_number = int(line_num_str.strip())
            if line_number in line_map:
                translated.append(SubtitleSegment(
                    line_number=line_number,
                    text=content.strip(),
                    start=line_map[line_number].start,
                    end=line_map[line_number].end
                ))
        except ValueError:
            continue
    
    return translated