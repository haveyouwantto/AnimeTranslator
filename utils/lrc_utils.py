from models.subtitle import Subtitle

def write_lrc_file(subtitle: Subtitle, output_path: str) -> None:
    with open(output_path, 'w', encoding='utf-8') as f:
        for seg in subtitle.segments:
            minutes = int(seg.start // 60)
            seconds = int(seg.start % 60)
            milliseconds = int((seg.start - int(seg.start)) * 100)
            f.write(f"[{minutes:02}:{seconds:02}.{milliseconds:02}]{seg.text}\n")