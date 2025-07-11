from abc import ABC, abstractmethod
from pathlib import Path
import pysubs2
from ..base_source import BaseSubtitleSource

class ASSource(BaseSubtitleSource):
    """ASS/SSA字幕源抽象基类"""
    def __init__(self):
        self.original_ass = None  # 保存原始ASS数据
        self._styles = None
        self._info = None
        self._events = None

    @property
    def styles(self):
        """获取ASS样式表"""
        return self.original_ass.styles if self.original_ass else None

    @property
    def info(self):
        """获取ASS文件头信息"""
        return self.original_ass.info if self.original_ass else None

    @property
    def events(self):
        """获取ASS事件(对话行)"""
        return self.original_ass.events if self.original_ass else None

    def get_plain_text(self) -> list[tuple[int, str]]:
        """提取纯文本和行号 (行号, 文本)"""
        if not self.original_ass:
            return []
        
        return [
            (i+1, event.text)  # ASS行号从1开始
            for i, event in enumerate(self.original_ass.events)
            if event.type == "Dialogue"
        ]
    
    def post_processing(self):
        pass