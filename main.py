import sys
import yaml
import argparse
from processor import SubtitleProcessor
from pathlib import Path
from config import create_default_config
import glob
import os

# 默认配置文件路径在脚本目录下
DEFAULT_CONFIG = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "config.yml")


def load_config(config_path=DEFAULT_CONFIG):
    """加载配置文件，不存在则创建"""
    if not Path(config_path).exists():
        print(f"未找到配置文件: {config_path}")
        if create_default_config(config_path):
            sys.exit(0)  # 创建成功后退出，让用户修改配置
        else:
            sys.exit(1)  # 创建失败时退出

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"加载配置文件失败: {str(e)}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Anime Translator - 自动生成并翻译视频/音频字幕")
    parser.add_argument("input_files", nargs="+", help="输入音频/视频文件（支持通配符 glob）")
    parser.add_argument("-e", "--env", help="指定配置文件路径 (默认: 脚本目录下的 config.yml)", default=DEFAULT_CONFIG)

    args = parser.parse_args()

    config = load_config(args.env)
    processor = SubtitleProcessor(config)
    
    for patt in args.input_files:
        result = glob.glob(patt)
        if result:
            for file in result:
                processor.process(file)
        else:
            processor.process(patt)


if __name__ == "__main__":
    main()
