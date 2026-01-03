import openai
from openai import OpenAI
import time
import math
from typing import Tuple, List
from models.subtitle import Subtitle, SubtitleSegment
from .base_translator import BaseTranslator
from utils.text_format import segments_to_text, text_to_segments, create_segment
import traceback
import logging

logger = logging.getLogger(__name__)


class OpenAITranslator(BaseTranslator):
    def __init__(
        self,
        api_key: str,
        api_base: str,
        model: str,
        prompt: str,
        temperature: float = 0.5,
        max_retries: int = 3,
        retry_delay: int = 5,
        batch_size: int = 20,
        history_size: int = 50,
        example_input: str = "0|Alice|天気がいいですね",
        example_output: str = "0|Alice|天气真好啊",
    ):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.prompt = prompt
        self.temperature = temperature
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.batch_size = batch_size

        # 如果 history_size 非整数，则向上取整
        self.history_size = math.ceil(history_size)

        self.example_input = example_input
        self.example_output = example_output
        self.client = OpenAI(base_url=api_base, api_key=api_key)



    def translate(self, subtitle: Subtitle) -> Subtitle:
        translated_segments = []

        # 初始化对话历史，保存原文和翻译对（以行单位）
        self.orig_segments = []
        self.trans_segments = []

        # 插入示例输入输出到segments
        split_input = self.example_input.split("|")
        split_output = self.example_output.split("|")
        example_input_segment = create_segment(
            split_input[0], split_input[2], split_input[1]
        )
        example_output_segment = create_segment(
            split_output[0], split_output[2], split_output[1]
        )
        self.orig_segments.append(example_input_segment)
        self.trans_segments.append(example_output_segment)

        # 按照 batch_size 进行批量翻译
        for i in range(0, len(subtitle.segments), self.batch_size):
            batch = subtitle.segments[i : i + self.batch_size]
            try:
                result = self._translate_batch(batch)
            except Exception as e:
                logger.warning(
                    f"Batch translation failed after retries, switching to line-by-line translation. Error: {str(e)}"
                )
                result = self._translate_line_by_line(batch)
            translated_segments.extend(result)
            time.sleep(self.retry_delay)

        logger.info("Translation completed")
        return Subtitle(translated_segments)

    def _build_messages(self, incoming_message: List[SubtitleSegment]) -> List[dict]:
        """
        构建对话消息，将系统提示、历史对话以及当前用户消息组合起来。
        历史对话按 batch_size 组成 role pair，以便更好利用 LLM 缓存。
        """
        messages = [{"role": "system", "content": self.prompt}]

        # 始终包含第一个示例片段作为第一个 role pair
        if len(self.orig_segments) > 0:
            messages.append({"role": "user", "content": segments_to_text([self.orig_segments[0]])})
            messages.append({"role": "assistant", "content": segments_to_text([self.trans_segments[0]])})

        # 剩余的历史记录（排除示例）
        h_orig = self.orig_segments[1:]
        h_trans = self.trans_segments[1:]

        if len(h_orig) > 0:
            # 限制历史记录数量，并按 batch_size 对齐以保持前缀稳定
            start = max(0, len(h_orig) - self.history_size)
            # 向上取整到 batch_size 的倍数，确保不超出 history_size 且对齐
            start = math.ceil(start / self.batch_size) * self.batch_size
            
            h_orig = h_orig[start:]
            h_trans = h_trans[start:]

            # 按 batch_size 分组并添加为 role pairs
            for i in range(0, len(h_orig), self.batch_size):
                chunk_orig = h_orig[i : i + self.batch_size]
                chunk_trans = h_trans[i : i + self.batch_size]
                if chunk_orig:
                    messages.append({"role": "user", "content": segments_to_text(chunk_orig)})
                    messages.append({"role": "assistant", "content": segments_to_text(chunk_trans)})

        # 添加当前待翻译的消息
        messages.append({"role": "user", "content": segments_to_text(incoming_message)})
        return messages

    def _translate_batch(self, batch: List[SubtitleSegment]) -> Tuple[list]:
        retries = 0
        while retries < self.max_retries:
            try:
                # 只发送行号和文本
                messages = self._build_messages(batch)

                response = self.client.chat.completions.create(model=self.model, messages=messages, temperature=self.temperature)

                translated_text = response.choices[0].message.content
                translated_segments = text_to_segments(translated_text, batch)

                # 检查翻译后的分段数量是否匹配
                if len(translated_segments) != len(batch):
                    error_msg = f"Translated segments count mismatch: expected {len(batch)}, got {len(translated_segments)}"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                logger.info(
                    f"Translated batch ending at line {batch[-1].line_number} successfully"
                )

                # 更新对话历史，记录当前批次的对话对（按行逐条添加）
                self.orig_segments.extend(batch)
                self.trans_segments.extend(translated_segments)

                return translated_segments

            except Exception as e:
                retries += 1
                logger.warning(
                    f"Retry {retries}/{self.max_retries} for batch ending at line {batch[-1].line_number} due to error: {str(e)}"
                )
                if retries >= self.max_retries:
                    logger.error("Max retries exceeded for batch translation")
                    raise Exception("Translation failed after retries") from e
                time.sleep(self.retry_delay * (2**retries))  # 指数退避

    def _translate_line_by_line(self, batch: list) -> list:
        """
        当一次批量翻译的行数不匹配并重试超过 max_retries 时，退化为逐行翻译。
        """
        translated_segments = []
        for segment in batch:
            retries = 0
            while retries < self.max_retries:
                try:
                    # 每次只翻译一行
                    segment_list = [segment]
                    messages = self._build_messages(segment_list)

                    response = self.client.chat.completions.create(model=self.model,
                    messages=messages,
                    temperature=self.temperature)

                    translated_text = response.choices[0].message.content
                    translated_segment = text_to_segments(translated_text, segment_list)

                    if len(translated_segment) != 1:
                        error_msg = f"Translated single segment count mismatch: expected 1, got {len(translated_segment)}"
                        logger.error(error_msg)
                        raise ValueError(error_msg)

                    logger.info(
                        f"Translated line {segment.line_number} successfully in line-by-line mode"
                    )

                    # 更新对话历史
                    self.orig_segments.append(segment)
                    print(translated_segment)
                    self.trans_segments.extend(translated_segment)

                    translated_segments.extend(translated_segment)
                    break  # 成功翻译当前行，退出重试循环
                except Exception as e:
                    retries += 1
                    logger.warning(
                        f"Retry {retries}/{self.max_retries} for line {segment.line_number} due to error: {str(e)}"
                    )
                    if retries >= self.max_retries:
                        logger.error(
                            f"Max retries exceeded for line {segment.line_number}"
                        )
                        raise Exception(
                            "Line-by-line translation failed after retries"
                        ) from e
                    time.sleep(self.retry_delay * (2**retries))  # 指数退避
        return translated_segments
