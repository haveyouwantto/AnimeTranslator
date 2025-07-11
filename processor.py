from typing import List
from models.subtitle import Subtitle
from sources.embedded_source import EmbeddedSource
from sources.srt_source import SRTSource
from sources.whisper_source import WhisperSource
from sources.ass.base import ASSource
from sources.ass.file import ASSFileSource
from sources.ass.embedded import ASSEmbeddedSource
from sources.ass.whisper_word import WhisperWord
from translators.openai_translator import OpenAITranslator
from utils.srt_utils import write_srt_file
from utils.ass_util import write_ass_file
import os


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
            ASSFileSource(),      # 先尝试外挂ASS
            ASSEmbeddedSource(),  # 然后尝试内嵌ASS
            SRTSource(),
            EmbeddedSource()
        ]

        if self.config['whisper']['enable']:
            self.sources.append(WhisperWord(
                model_size=self.config['whisper']['model_size'],
                language=self.config['whisper']['language'],
                beam_size=self.config['whisper']['beam_size']
            ))
    
    def _init_translator(self):
        self.translator = OpenAITranslator(
            api_key=self.config['openai']['api_key'],
            api_base=self.config['openai']['api_base'],
            model=self.config['openai']['model'],
            prompt=self.config['translation']['prompt'],
            temperature=self.config['openai']['temperature'],
            max_retries=self.config['translation']['max_retries'],
            retry_delay=self.config['translation']['retry_delay'],
            batch_size=self.config['translation']['batch_size'],
            history_size=self.config['translation']['history_size'],
            example_input=self.config['translation']['example_input'],
            example_output=self.config['translation']['example_output']
        )
    
    def process(self, audio_path: str) -> None:
        if not os.path.exists(audio_path):
            logger.error("File not found")
            return
        logger.info("Processing file: "+ audio_path)    
        result = self._get_subtitle(audio_path)
        if not result:
            logger.error("No subtitle found for %s", audio_path)
            return
        source, subtitle = result
        logger.info("Found subtitle with %d lines"%len(subtitle.segments))
        translated = self.translator.translate(subtitle)
        if isinstance(source, ASSource):
            source.post_processing()
            write_ass_file(source, translated, f"{audio_path}.zh.ass")
            logger.info("ASS file successfully written")
        else:
            write_srt_file(translated, f"{audio_path}.zh.srt")
            logger.info("SRT file successfully written")
    
    def _get_subtitle(self, audio_path: str) -> Subtitle:
        if self.config['common']['ignore_subtitles']:
            return self.sources[-1], self.sources[-1].get_subtitle(audio_path)
        
        for source in self.sources:
            try:
                logger.info("Try source: "+ str(source.__class__.__name__))
                sub =  source.get_subtitle(audio_path)
                if sub:
                    return source, sub
            except Exception:
                continue
        return self.sources[-1], self.sources[-1].get_subtitle(audio_path)