from models.subtitle import Subtitle

def seconds_to_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"

def write_srt_file(subtitle: Subtitle, output_path: str) -> None:
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(subtitle.segments):
            f.write(f"{i+1}\n")
            f.write(f"{seconds_to_srt_time(seg.start)} --> {seconds_to_srt_time(seg.end)}\n")
            f.write(f"{seg.text}\n\n")