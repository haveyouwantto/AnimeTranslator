from models.subtitle import SubtitleSegment

def segments_to_text(segments: list[SubtitleSegment]) -> str:
    """将字幕片段转换为纯文本格式(只包含行号和文本)"""
    return "\n".join(
        f"{seg.line_number}|{seg.character}|{seg.text}"
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
        
        line_num_str, character, content = line.split("|", 2)
        try:
            line_number = int(line_num_str.strip())
            if line_number in line_map:
                translated.append(SubtitleSegment(
                    line_number=line_number,
                    text=content.strip(),
                    start=line_map[line_number].start,
                    end=line_map[line_number].end,
                    character=character
                ))
        except ValueError:
            continue
    
    return translated

def create_segment(line: int, text: str, character: str, start: float = 0.0, end: float = 0.0) -> SubtitleSegment:
    """创建一个新的 SubtitleSegment 对象。

    Args:
        line: 字幕的行号。
        text: 字幕的文本内容。
        character: 说话的角色。
        start: 字幕开始时间 (秒). Defaults to 0.0.
        end: 字幕结束时间 (秒). Defaults to 0.0.

    Returns:
        一个新的 SubtitleSegment 对象.
    """
    return SubtitleSegment(
        line_number=line,
        text=text,
        start=start,
        end=end,
        character=character
    )