from typing import List
from models.subtitle import Subtitle
from sources.embedded_source import EmbeddedSource
from sources.srt_source import SRTSource
from sources.whisper_source import WhisperSource
from translators.openai_translator import OpenAITranslator
from utils.srt_utils import write_srt_file


import logging
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class SubtitleProcessor:
    def __init__(self, config: dict):
        self.config = config
        self._init_sources()
        self._init_translator()
    
    def _init_sources(self):
        self.sources = [
            SRTSource(),
            EmbeddedSource(),
            WhisperSource(
                model_size=self.config['whisper']['model_size'],
                language=self.config['whisper']['language'],
                beam_size=self.config['whisper']['beam_size']
            )
        ]
    
    def _init_translator(self):
        self.translator = OpenAITranslator(
            api_key=self.config['openai']['api_key'],
            api_base=self.config['openai']['api_base'],
            model=self.config['openai']['model'],
            prompt=self.config['translation']['prompt'],
            temperature=self.config['openai']['temperature'],
            max_retries=self.config['translation']['max_retries'],
            retry_delay=self.config['translation']['retry_delay']
        )
    
    def process(self, audio_path: str) -> None:
        subtitle = self._get_subtitle(audio_path)
        logger.info("Found subtitle with %d lines"%len(subtitle.segments))
        translated = self.translator.translate(subtitle)
        write_srt_file(translated, f"{audio_path}.zh.srt")
    
    def _get_subtitle(self, audio_path: str) -> Subtitle:
        if self.config['common']['ignore_subtitles']:
            return self.sources[-1].get_subtitle(audio_path)
        
        for source in self.sources:
            try:
                logger.info("Try source: "+ str(source.__class__.__name__))
                return source.get_subtitle(audio_path)
            except Exception:
                continue
        return self.sources[-1].get_subtitle(audio_path)