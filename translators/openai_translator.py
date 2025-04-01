import openai
import time
from typing import Tuple
from models.subtitle import Subtitle, SubtitleSegment
from .base_translator import BaseTranslator
from utils.text_format import segments_to_text, text_to_segments
import traceback

import logging
logger = logging.getLogger(__name__)

class OpenAITranslator(BaseTranslator):
    def __init__(self, api_key: str, api_base: str, model: str, 
                 prompt: str, temperature: float = 0.5,
                 max_retries: int = 3, retry_delay: int = 5, batch_size: int = 20, 
                 example_input:str="1|天気がいいですね",
                 example_output:str='1|天气真好啊'
                 ):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.prompt = prompt
        self.temperature = temperature
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.batch_size = batch_size
        self.example_input = example_input
        self.example_output = example_output
        openai.api_key = api_key
        openai.api_base = api_base
    
    def translate(self, subtitle: Subtitle) -> Subtitle:
        translated_segments = []
        last_line = {"role": "user", "content": self.example_input}
        last_translation = {"role": "assistant", "content": self.example_output}
        
        for i in range(0, len(subtitle.segments), self.batch_size):
            batch = subtitle.segments[i:i+self.batch_size]
            result, last_line, last_translation = self._translate_batch(
                batch, last_line, last_translation
            )
            translated_segments.extend(result)
            time.sleep(self.retry_delay)
        
        logger.info("Translation completed")
        return Subtitle(translated_segments)
    
    def _translate_batch(self, batch: list, last_line: dict, 
                        last_translation: dict) -> Tuple[list, dict, dict]:
        retries = 0
        while retries < self.max_retries:
            try:
                # 只发送行号和文本
                text_content = segments_to_text(batch)
                line = {"role": "user", "content": text_content}
                
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": self.prompt},
                        last_line, last_translation, line
                    ],
                    temperature=self.temperature
                )
                
                # 解析回复并重新关联时间信息
                translated_text = response["choices"][0]["message"]["content"]
                translated_segments = text_to_segments(translated_text, batch)
                
                # 检查翻译后的分段数量是否匹配
                if len(translated_segments) != len(batch):
                    error_msg = f"Translated segments count mismatch: expected {len(batch)}, got {len(translated_segments)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                
                logger.info(f"Translated line {batch[-1].line_number} successfully")
                return translated_segments, line, response["choices"][0]["message"]
            
            except Exception as e:
                retries += 1
                logger.warning(f"Retry {retries}/{self.max_retries} due to error: {str(e)}")
                if retries >= self.max_retries:
                    logger.error("Max retries exceeded, raising exception")
                    raise Exception("Translation failed after retries") from e
                time.sleep(self.retry_delay * retries)  # 指数退避