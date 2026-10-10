
import os
import random
import subprocess
from datetime import datetime, timezone

os.makedirs("videos", exist_ok=True)
os.makedirs("clips", exist_ok=True)

DURATION = 20
FPS = 30
W, H = 1080, 1920

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

STYLES = [
    {
        "name": "CINEMATIC",
        "color": "contrast=1.18:saturation=1.12:brightness=-0.04",
        "quotes": [
            "MOVE IN SILENCE",
            "BUILT DIFFERENT",
            "LET SUCCESS SPEAK"
        ]
    },
    {
        "name": "VIRAL",
        "color": "contrast=1.12:saturation=1.25:brightness=0",
        "quotes": [
            "YOUR TIME IS NOW",
            "NO EXCUSES",
            "CHASE THE VISION"
        ]
    },
    {
        "name": "PREMIUM",
        "color": "contrast=1.08:saturation=0.92:brightness=0.01",
        "quotes": [
            "FREEDOM IS THE REAL LUXURY",
            "CREATE YOUR OWN LEGACY",
            "DREAM BIGGER"
        ]
    }
]

VIDEO_EXT = (".mp4", ".mov", ".mkv", ".webm")

clips = [
    os.path.join("clips", f)
    for f in os.listdir("clips")
    if f.lower().endswith(VIDEO_EXT)
]

if not clips:
    raise SystemExit("ERROR: Add video clips to the clips folder.")

if not os.path.exists(FONT):
    raise SystemExit("ERROR: Font missing.")

random.shuffle(clips)
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

for i in range(3):
    style = STYLES[i]
    clip = clips[i % len(clips)]
    quote = random.choice(style["quotes"])

    output = f"videos/luxury_{today}_{i + 1}.mp4"
    text_file = f"videos/quote_{i + 1}.txt"

    with open(text_file, "w", encoding="utf-8") as f:
        f.write(quote)

    video_filter = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},"
        "setsar=1,"
        f"eq={style['color']},"
        "drawbox=x=0:y=ih*0.59:w=iw:h=ih*0.25:"
        "color=black@0.38:t=fill,"
        f"drawtext=fontfile={FONT}:"
        f"textfile={text_file}:"
        "fontcolor=white:"
        "fontsize=64:"
        "x=(w-text_w)/2:"
        "y=(h-text_h)/2:"
        "shadowcolor=black@0.8:"
        "shadowx=3:shadowy=3:"
        "borderw=1:bordercolor=white@0.25,"
        "fade=t=in:st=0:d=0.5,"
        f"fade=t=out:st={DURATION - 1}:d=1"
    )

    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", clip,
        "-filter_complex",
        f"[0:v]{video_filter},split=2[first][second];"
        f"[first][second]concat=n=2:v=1:a=0[outv]",
        "-map", "[outv]",
        "-t", str(DURATION),
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "21",
        "-pix_fmt", "yuv420p",
        "-an",
        "-movflags", "+faststart",
        output
    ]

    print(f"Creating {style['name']} video: {output}")
    subprocess.run(cmd, check=True)
    print(f"SUCCESS: {output}")

print("Luxury Life AI finished!")
