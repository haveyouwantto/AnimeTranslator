from pathlib import Path
import pysubs2
from models.subtitle import Subtitle
from sources.ass.base import ASSource

def write_ass_file(source: ASSource, subtitle: Subtitle, output_path: str) -> bool:
    """
    将翻译后的字幕写入ASS文件，保留原始样式和格式
    
    Args:
        source: 原始ASS数据源
        subtitle: 翻译后的字幕数据
        output_path: 输出文件路径
    
    Returns:
        bool: 是否成功
    """
    if not source.original_ass:
        return False
    
    # 创建ASS文件副本
    translated_ass = source.original_ass
    
    # 构建行号到文本的映射
    translation_map = {
        seg.line_number: seg.text
        for seg in subtitle.segments
    }
    
    # 只替换对话文本，保留所有样式和格式
    event_index = 0
    for event in translated_ass.events:
        if event.type == "Dialogue":
            event_index += 1
            if event_index in translation_map:
                event.text = translation_map[event_index]
    
    try:
        translated_ass.save(output_path)
        return True
    except Exception as e:
        return False