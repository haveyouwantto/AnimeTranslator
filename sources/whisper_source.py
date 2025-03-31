
from models.subtitle import Subtitle, SubtitleSegment
from .base_source import BaseSubtitleSource

class WhisperSource(BaseSubtitleSource):
    def __init__(self, model_size: str, language: str, beam_size: int = 5):
        self.model_size = model_size
        self.language = language
        self.beam_size = beam_size
    
    def _load_model(self):
        from faster_whisper import WhisperModel
        import torch
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        compute_type = 'float32'
        self.model = WhisperModel(self.model_size, device, compute_type=compute_type)
    
    def get_subtitle(self, audio_path: str) -> Subtitle:
        self._load_model()
        segments, _ = self.model.transcribe(
            audio_path,
            beam_size=self.beam_size,
            language=self.language
        )
        subtitle_segments = [
            SubtitleSegment(
                start=segment.start,
                end=segment.end,
                text=segment.text,
                line_number=i+1  # Whisper生成的行号从1开始
            ) for i, segment in enumerate(segments)
        ]
        return Subtitle(subtitle_segments)