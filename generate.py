
import os
import random
import subprocess
from datetime import datetime, timezone

os.makedirs("videos", exist_ok=True)

DURATION = 20
FPS = 30
W, H = 1080, 1920
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

STYLES = [
    {
        "name": "CINEMATIC",
        "color": "contrast=1.22:saturation=1.18:brightness=-0.035",
        "quotes": ["MOVE IN SILENCE", "BUILT DIFFERENT", "LET SUCCESS SPEAK"]
    },
    {
        "name": "VIRAL",
        "color": "contrast=1.18:saturation=1.28:brightness=-0.01",
        "quotes": ["YOUR TIME IS NOW", "NO EXCUSES", "CHASE THE VISION"]
    },
    {
        "name": "PREMIUM",
        "color": "contrast=1.14:saturation=1.05:brightness=-0.02",
        "quotes": ["FREEDOM IS THE REAL LUXURY", "CREATE YOUR OWN LEGACY", "DREAM BIGGER"]
    }
]

VIDEO_EXT = (".mp4", ".mov", ".mkv", ".webm")
AUDIO_EXT = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")

clips = [
    os.path.join("clips", f)
    for f in os.listdir("clips")
    if f.lower().endswith(VIDEO_EXT)
]

music = [
    os.path.join("music", f)
    for f in os.listdir("music")
    if f.lower().endswith(AUDIO_EXT)
]

if not clips:
    raise SystemExit("ERROR: Add video clips to clips folder.")
if not music:
    raise SystemExit("ERROR: Add music to music folder.")
if not os.path.exists(FONT):
    raise SystemExit("ERROR: Font missing.")

random.shuffle(clips)
random.shuffle(music)

today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

for i in range(3):
    style = STYLES[i]
    clip = clips[i % len(clips)]
    track = music[i % len(music)]
    quote = random.choice(style["quotes"])

    output = f"videos/luxury_{today}_{i + 1}.mp4"
    text_file = f"videos/quote_{i + 1}.txt"

    with open(text_file, "w", encoding="utf-8") as f:
        f.write(quote)

    video_filter = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1,"
        "zoompan=z='min(zoom+0.0007,1.10)':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d=1:s={W}x{H}:fps={FPS},"
        f"eq={style['color']},"
        "vignette=PI/5,"
        "drawbox=x=0:y=ih*0.58:w=iw:h=ih*0.27:"
        "color=black@0.42:t=fill,"
        f"drawtext=fontfile={FONT}:textfile={text_file}:"
        "fontcolor=white:fontsize=66:"
        "x=(w-text_w)/2:y=(h-text_h)/2:"
        "shadowcolor=black@0.9:shadowx=4:shadowy=4:"
        "borderw=2:bordercolor=black@0.3,"
        "fade=t=in:st=0:d=0.7,"
        f"fade=t=out:st={DURATION - 1}:d=1"
    )

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", clip,
        "-stream_loop", "1", "-i", track,
        "-filter_complex",
        f"[0:v]{video_filter},split=2[first][second];"
        "[first][second]concat=n=2:v=1:a=0[outv]",
        "-map", "[outv]",
        "-map", "1:a:0",
        "-t", str(DURATION),
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-af",
        "volume=0.18,afade=t=in:st=0:d=1,"
        f"afade=t=out:st={DURATION - 2}:d=2",
        "-c:a", "aac",
        "-b:a", "160k",
        "-shortest",
        "-movflags", "+faststart",
        output
    ]

    print(f"Creating {style['name']} video: {output}")
    subprocess.run(cmd, check=True)
    print(f"SUCCESS: {output}")

print("Luxury Life AI finished!")
