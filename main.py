import sys
import yaml
from processor import SubtitleProcessor

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py audio_file.mp3")
        sys.exit(1)
    
    with open('config.yml', 'r') as f:
        config = yaml.safe_load(f)
    
    processor = SubtitleProcessor(config)
    processor.process(sys.argv[1])

if __name__ == "__main__":
    main()