def srt_time_to_seconds(srt_time: str) -> float:
    hours, rest = srt_time.split(':', 1)
    minutes, rest = rest.split(':', 1)
    seconds, milliseconds = rest.split(',')
    return float(hours)*3600 + float(minutes)*60 + float(seconds) + float(milliseconds)/1000