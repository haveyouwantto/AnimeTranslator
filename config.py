import os
import yaml

DEFAULT_CONFIG = """
# config.yml

common:
  ignore_subtitles: False

whisper:
  enable: True
  model_size: "large-v3"
  beam_size: 5
  language: "auto"
  condition_on_previous_text: False

openai:
  api_key: "your-api-key-here"
  api_base: "https://api.openai.com/v1"
  model: "gpt-4"
  temperature: 0.3

translation:
  prompt: |
    你是一位专业翻译专家，请严格遵循以下规则翻译带行号的日本番剧字幕，翻译成中文：
    1. 输入输出均使用格式：line|character|text\\n
    其中line是行号数，text是文本内容，character是角色名，有可能留空
    2. 必须直接输出，禁止包含```等代码块符号或任何额外文本
    3. 翻译要求：
       - 完全保留所有形容词（包括程度副词和情感修饰词）
       - 不能丢掉原文的任何词汇
       - 输出的行数必须与原文保持一致
       - 保持原文的表达方式，保留所有感叹词（例：ええ、あの）
       - 中文译文需与原文情感强度完全一致
       - 必须翻译人名和罗马音(Misaka->御坂，禁止保留原文)
       - 保持上下文称谓统一（角色称呼前后一致）
       - 保留所有格式标记，比如html标签或ssa标记（如有）
    4. 错误示例：
       Bad: ```0|Alice|你好``` (含代码块)
       Bad: 你好 (缺少行号)
    5. 必须返回格式：行号|角色名|翻译内容
    任何格式错误将导致系统故障，请确保输出格式正确！
  example_input: '0|Narrator|Welcome to our show, let the story begin!'
  example_output: '0|旁白|欢迎观看本节目，让我们开始故事吧！'
  batch_size: 50
  history_size: 500
  request_interval: 1  # seconds between requests
  max_retries: 5       # max number of retries for translation
  retry_delay: 5       # seconds to wait before retrying translation

output:
  lrc_format: False  # If true, output LRC files; if false, output SRT/ASS files
"""

def create_default_config(config_path='config.yml'):
    """创建默认配置文件"""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(DEFAULT_CONFIG.strip())
        print(f"已创建默认配置文件: {os.path.abspath(config_path)}")
        print("请修改配置文件中的API密钥等必要信息后再运行程序")
        return True
    except Exception as e:
        print(f"创建配置文件失败: {str(e)}")
        return False