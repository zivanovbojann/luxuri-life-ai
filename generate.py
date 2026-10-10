
import os
import random
import subprocess
import requests
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

VIDEO_DIR = Path("videos")
CLIP_DIR = Path("clips")
MUSIC_DIR = Path("music")

for folder in (VIDEO_DIR, CLIP_DIR, MUSIC_DIR):
    folder.mkdir(parents=True, exist_ok=True)

DURATION = 20
FPS = 30
W, H = 1080, 1920
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
API_KEY = os.getenv("PIXABAY_API_KEY", "").strip()

VIDEO_EXT = (".mp4", ".mov", ".mkv", ".webm")
AUDIO_EXT = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")

SEARCH_TERMS = [
    "luxury car night",
    "luxury mansion",
    "luxury lifestyle",
    "supercar driving",
    "luxury watch",
    "private jet luxury",
    "luxury city night",
    "sports car cinematic",
    "luxury car cinematic vertical",
    "supercar sunset",
]

STYLES = [
    {
        "name": "CINEMATIC",
        "color": "contrast=1.22:saturation=1.18:brightness=-0.035",
        "quotes": [
            "MOVE IN SILENCE",
            "BUILT DIFFERENT",
            "LET SUCCESS SPEAK",
            "DISCIPLINE BUILDS LEGENDS",
            "WORK UNTIL THEY NOTICE",
        ],
    },
    {
        "name": "VIRAL",
        "color": "contrast=1.18:saturation=1.28:brightness=-0.01",
        "quotes": [
            "YOUR TIME IS NOW",
            "NO EXCUSES",
            "CHASE THE VISION",
            "STAY HUNGRY",
            "PROVE THEM WRONG",
        ],
    },
    {
        "name": "PREMIUM",
        "color": "contrast=1.14:saturation=1.05:brightness=-0.02",
        "quotes": [
            "FREEDOM IS THE REAL LUXURY",
            "CREATE YOUR OWN LEGACY",
            "DREAM BIGGER",
            "SUCCESS IS A LIFESTYLE",
            "THINK BEYOND LIMITS",
        ],
    },
]


def download_pixabay_clip():
    if not API_KEY:
        print("Nema PIXABAY_API_KEY.")
        return None

    terms = SEARCH_TERMS.copy()
    random.shuffle(terms)

    for term in terms:
        try:
            response = requests.get(
                "https://pixabay.com/api/videos/",
                params={
                    "key": API_KEY,
                    "q": term,
                    "safesearch": "true",
                    "per_page": 50,
                    "order": "popular",
                },
                timeout=30,
            )
            response.raise_for_status()
            hits = response.json().get("hits", [])
            random.shuffle(hits)

            for hit in hits:
                video_id = str(hit.get("id", ""))
                if not video_id:
                    continue

                destination = CLIP_DIR / f"pixabay_{video_id}.mp4"

                if destination.exists():
                    continue

                options = hit.get("videos", {})
                video = (
                    options.get("large")
                    or options.get("medium")
                    or options.get("small")
                )

                if not video or not video.get("url"):
                    continue

                temporary = destination.with_suffix(".part")

                try:
                    with requests.get(
                        video["url"], stream=True, timeout=90
                    ) as video_response:
                        video_response.raise_for_status()
                        with open(temporary, "wb") as output:
                            for chunk in video_response.iter_content(
                                chunk_size=1024 * 1024
                            ):
                                if chunk:
                                    output.write(chunk)

                    if (
                        not temporary.exists()
                        or temporary.stat().st_size < 100_000
                    ):
                        temporary.unlink(missing_ok=True)
                        continue

                    temporary.replace(destination)

                    with open(
                        CLIP_DIR / "pixabay_sources.txt",
                        "a",
                        encoding="utf-8",
                    ) as source_file:
                        source_file.write(
                            f"ID: {video_id} | "
                            f"Autor: {hit.get('user', 'unknown')} | "
                            f"Link: {hit.get('pageURL', '')}\n"
                        )

                    print(f"Preuzet novi klip: {destination}")
                    return str(destination)

                except Exception as error:
                    print(f"Klip nije preuzet: {error}")
                    temporary.unlink(missing_ok=True)

        except Exception as error:
            print(f"Pixabay pretraga nije uspela: {error}")

    return None


def get_existing_clips():
    return [
        str(path)
        for path in CLIP_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXT
    ]


def get_music():
    return [
        str(path)
        for path in MUSIC_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in AUDIO_EXT
    ]


def main():
    # Ukloni stare MP4 izlaze da upload skripta ne obrađuje
    # više videa u istom pokretanju.
    for path in VIDEO_DIR.glob("*.mp4"):
        path.unlink()

    for path in VIDEO_DIR.glob("quote_*.txt"):
        path.unlink()

    if not Path(FONT).exists():
        raise SystemExit("ERROR: Font nije pronađen.")

    music = get_music()
    if not music:
        raise SystemExit("ERROR: Dodaj MP3 muziku u folder music/.")

    clip = download_pixabay_clip()

    if not clip:
        existing = get_existing_clips()
        if not existing:
            raise SystemExit("ERROR: Nema dostupnih video-klipova.")
        clip = random.choice(existing)

    track = random.choice(music)
    style = random.choice(STYLES)
    quote = random.choice(style["quotes"])

    now = datetime.now(ZoneInfo("Europe/Berlin"))
    timestamp = now.strftime("%Y-%m-%d_%H-%M")
    output = VIDEO_DIR / f"luxury_{timestamp}.mp4"
    text_file = VIDEO_DIR / "quote_1.txt"
    text_file.write_text(quote, encoding="utf-8")

    video_filter = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1,"
        "zoompan=z='min(zoom+0.0007,1.10)':"
        "x='iw/2-(iw/zoom/2)':"
        "y='ih/2-(ih/zoom/2)':"
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

    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-stream_loop", "-1", "-i", clip,
        "-stream_loop", "-1", "-i", track,
        "-vf", video_filter,
        "-map", "0:v:0",
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
        "-movflags", "+faststart",
        str(output),
    ]

    print(f"Pravim jedan {style['name']} video: {output}")
    subprocess.run(command, check=True)
    print(f"USPEŠNO: {output}")
    print("Napravljeno videa: 1")


if __name__ == "__main__":
    main()
