
import os
import random
import subprocess
from datetime import datetime

os.makedirs("videos", exist_ok=True)
os.makedirs("clips", exist_ok=True)

quotes = [
    ("Luxury Lifestyle", "BUILD THE LIFE YOU DREAM OF."),
    ("Dream Big", "WORK IN SILENCE. LET SUCCESS SPEAK."),
    ("Freedom", "TRUE LUXURY IS FREEDOM."),
]

clips = [
    file for file in os.listdir("clips")
    if file.lower().endswith((".mp4", ".mov", ".mkv"))
]

if not clips:
    print("No video clips found in the clips folder.")
    print("Add legally usable car or luxury lifestyle videos to clips/.")
    raise SystemExit(0)

random.shuffle(clips)
today = datetime.now().strftime("%Y-%m-%d")

for number, (topic, quote) in enumerate(quotes, start=1):
    clip = clips[(number - 1) % len(clips)]
    source = os.path.join("clips", clip)
    output = f"videos/short_{today}_{number}.mp4"

    command = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", source,
        "-t", "20",
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        "drawtext=text='" + quote.replace("'", "") + "':"
        "fontcolor=white:fontsize=58:"
        "x=(w-text_w)/2:y=h*0.72:"
        "box=1:boxcolor=black@0.45:boxborderw=20",
        "-an",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Created video: {output}")
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        print(f"Could not create {output}: {error}")
        raise

print("Luxury Life AI finished!")
