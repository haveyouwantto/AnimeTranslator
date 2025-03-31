from abc import ABC, abstractmethod
from models.subtitle import Subtitle

class BaseTranslator(ABC):
    @abstractmethod
    def translate(self, subtitle: Subtitle) -> Subtitle:
        """翻译字幕"""
        pass