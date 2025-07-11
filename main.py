import sys
import yaml
from processor import SubtitleProcessor
from pathlib import Path
from config import create_default_config
import glob
import os

default_config = os.path.join( os.path.dirname(os.path.abspath(__file__)), "config.yml")

def load_config(config_path=default_config):
    """加载配置文件，不存在则创建"""
    if not Path(config_path).exists():
        print("未找到配置文件")
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
    if len(sys.argv) <= 1:
        print("Usage: python main.py audio_file.mp3 ...")
        sys.exit(1)
    
    
    config = load_config()
    processor = SubtitleProcessor(config)
    for patt in sys.argv[1:]:
    	for audio_file in glob.glob(patt):
            processor.process(audio_file)

if __name__ == "__main__":
    main()