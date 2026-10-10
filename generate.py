import os
import random
import subprocess
from datetime import datetime, timezone

# Luxury Life AI 2.0
# Automatic cinematic YouTube Shorts generator

os.makedirs("videos", exist_ok=True)
os.makedirs("clips", exist_ok=True)
os.makedirs("music", exist_ok=True)

VIDEO_DURATION = 20
VIDEO_COUNT = 3
WIDTH = 1080
HEIGHT = 1920
FPS = 30

QUOTES = [
    "BUILD THE LIFE YOU DREAM OF",
    "WORK IN SILENCE. WIN IN STYLE.",
    "DISCIPLINE CREATES FREEDOM",
    "DREAM BIG. STAY FOCUSED.",
    "YOUR FUTURE IS BUILT TODAY",
    "SUCCESS IS A LIFESTYLE",
    "FOCUS ON YOUR OWN JOURNEY",
    "MAKE YOUR DREAMS YOUR REALITY",
    "BE DIFFERENT. THINK BIGGER.",
    "NEVER STOP BUILDING YOUR FUTURE",
    "PRIVATE LIFE. BIG DREAMS.",
    "LET YOUR SUCCESS SPEAK",
    "LUXURY IS EARNED, NOT GIVEN",
    "STAY HUNGRY. STAY HUMBLE.",
    "ONE DAY OR DAY ONE. YOU DECIDE."
]

VIDEO_EXTENSIONS = (".mp4", ".mov", ".mkv", ".webm")
AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".aac", ".ogg")

clips = [
    os.path.join("clips", file)
    for file in os.listdir("clips")
    if file.lower().endswith(VIDEO_EXTENSIONS)
]

music_files = [
    os.path.join("music", file)
    for file in os.listdir("music")
    if file.lower().endswith(AUDIO_EXTENSIONS)
]

if not clips:
    print("ERROR: No videos found in the clips folder.")
    raise SystemExit(1)

# Use a reliable font available on GitHub Actions.
font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

if not os.path.exists(font):
    print("ERROR: Required font was not found.")
    raise SystemExit(1)

today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

print("====================================")
print("       LUXURY LIFE AI 2.0")
print("====================================")
print(f"Available video clips: {len(clips)}")
print(f"Available music tracks: {len(music_files)}")
print(f"Videos to create: {VIDEO_COUNT}")

random.shuffle(clips)
random.shuffle(music_files)

for number in range(1, VIDEO_COUNT + 1):

    clip = clips[(number - 1) % len(clips)]
    quote = random.choice(QUOTES)

    output = f"videos/luxury_short_{today}_{number}.mp4"

    print(f"\nCreating video {number}/{VIDEO_COUNT}")
    print(f"Source: {clip}")
    print(f"Quote: {quote}")

    # Cinematic color grading and a dark text background.
    video_filter = (
        f"scale={WIDTH}:{HEIGHT}:"
        "force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},"
        "setsar=1,"
        "eq=contrast=1.12:saturation=1.15:brightness=-0.03,"
        "drawbox=x=0:y=ih*0.61:w=iw:h=ih*0.25:"
        "color=black@0.38:t=fill,"
        f"drawtext=fontfile={font}:"
        f"text='{quote}':"
        "fontcolor=white:"
        "fontsize=54:"
        "line_spacing=15:"
        "x=(w-text_w)/2:"
        "y=(h-text_h)/2:"
        "box=1:"
        "boxcolor=black@0.20:"
        "boxborderw=18"
    )

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-stream_loop", "-1",
        "-i", clip,
    ]

    # Add music when a track is available.
    if music_files:
        music = music_files[(number - 1) % len(music_files)]
        command.extend([
            "-stream_loop", "-1",
            "-i", music
        ])

    command.extend([
        "-vf", video_filter,
        "-t", str(VIDEO_DURATION),
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
    ])

    if music_files:
        command.extend([
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-af", "volume=0.18",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
        ])
    else:
        command.append("-an")

    command.extend([
        "-movflags", "+faststart",
        output
    ])

    try:
        subprocess.run(command, check=True)
        print(f"SUCCESS: {output}")

    except subprocess.CalledProcessError as error:
        print(f"ERROR while creating video {number}: {error}")
        raise

print("\n====================================")
print("LUXURY LIFE AI 2.0 FINISHED!")
print(f"Videos saved in: videos/")
print("====================================")
