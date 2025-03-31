from abc import ABC, abstractmethod
from models.subtitle import Subtitle

class BaseSubtitleSource(ABC):
    @abstractmethod
    def get_subtitle(self, audio_path: str) -> Subtitle:
        """从给定音频/视频路径获取字幕"""
        pass