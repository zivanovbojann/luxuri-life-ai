
import os
import random
import subprocess
import requests
from datetime import datetime, timezone
from pathlib import Path

# LUXURY LIFE AI

os.makedirs("videos", exist_ok=True)
os.makedirs("clips", exist_ok=True)
os.makedirs("music", exist_ok=True)

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
]

STYLES = [
    {
        "name": "CINEMATIC",
        "color": "contrast=1.22:saturation=1.18:brightness=-0.035",
        "quotes": [
            "MOVE IN SILENCE",
            "BUILT DIFFERENT",
            "LET SUCCESS SPEAK"
        ]
    },
    {
        "name": "VIRAL",
        "color": "contrast=1.18:saturation=1.28:brightness=-0.01",
        "quotes": [
            "YOUR TIME IS NOW",
            "NO EXCUSES",
            "CHASE THE VISION"
        ]
    },
    {
        "name": "PREMIUM",
        "color": "contrast=1.14:saturation=1.05:brightness=-0.02",
        "quotes": [
            "FREEDOM IS THE REAL LUXURY",
            "CREATE YOUR OWN LEGACY",
            "DREAM BIGGER"
        ]
    }
]


def download_pixabay_clips(target_count=3):
    """Pretražuje Pixabay i preuzima do tri video-klipa."""

    if not API_KEY:
        print("Pixabay API key nije podešen. Koristim postojeće klipove.")
        return []

    downloaded = []
    seen_ids = set()
    terms = SEARCH_TERMS.copy()
    random.shuffle(terms)

    for term in terms:
        if len(downloaded) >= target_count:
            break

        try:
            response = requests.get(
                "https://pixabay.com/api/videos/",
                params={
                    "key": API_KEY,
                    "q": term,
                    "safesearch": "true",
                    "per_page": 20,
                    "order": "popular",
                },
                timeout=30,
            )
            response.raise_for_status()
            results = response.json()

            if "hits" not in results:
                print("Pixabay nije vratio rezultate. Proveri API ključ.")
                continue

            hits = results.get("hits", [])
            random.shuffle(hits)

            for hit in hits:
                if len(downloaded) >= target_count:
                    break

                video_id = str(hit.get("id", ""))

                if not video_id or video_id in seen_ids:
                    continue

                seen_ids.add(video_id)

                video_options = hit.get("videos", {})
                video = (
                    video_options.get("large")
                    or video_options.get("medium")
                    or video_options.get("small")
                )

                if not video or not video.get("url"):
                    continue

                destination = Path("clips") / f"pixabay_{video_id}.mp4"

                if destination.exists() and destination.stat().st_size > 100_000:
                    downloaded.append(str(destination))
                    continue

                temporary = destination.with_suffix(".part")

                try:
                    with requests.get(
                        video["url"],
                        stream=True,
                        timeout=60
                    ) as video_response:
                        video_response.raise_for_status()

                        with open(temporary, "wb") as output_file:
                            for chunk in video_response.iter_content(
                                chunk_size=1024 * 1024
                            ):
                                if chunk:
                                    output_file.write(chunk)

                    if temporary.stat().st_size < 100_000:
                        temporary.unlink(missing_ok=True)
                        continue

                    temporary.replace(destination)
                    downloaded.append(str(destination))

                    # Evidencija izvora klipa
                    with open(
                        "clips/pixabay_sources.txt",
                        "a",
                        encoding="utf-8"
                    ) as source_file:
                        source_file.write(
                            f"ID: {video_id} | "
                            f"Autor: {hit.get('user', 'unknown')} | "
                            f"Link: {hit.get('pageURL', '')}\n"
                        )

                    print(f"Preuzet klip: {destination}")

                except Exception as error:
                    print(f"Preuzimanje klipa nije uspelo: {error}")
                    temporary.unlink(missing_ok=True)

        except Exception as error:
            print(f"Pixabay pretraga za '{term}' nije uspela: {error}")

    return downloaded


def get_clips():
    return [
        str(Path("clips") / filename)
        for filename in os.listdir("clips")
        if filename.lower().endswith(VIDEO_EXT)
        and (Path("clips") / filename).is_file()
    ]


def get_music():
    return [
        str(Path("music") / filename)
        for filename in os.listdir("music")
        if filename.lower().endswith(AUDIO_EXT)
        and (Path("music") / filename).is_file()
    ]


# 1. Automatski pronađi video-klipove
download_pixabay_clips(target_count=3)

clips = get_clips()
music = get_music()

if not clips:
    raise SystemExit(
        "ERROR: Nema klipova. Proveri Pixabay API ključ ili folder clips."
    )

if not music:
    raise SystemExit(
        "ERROR: Nema muzike. Dodaj licenciranu muziku u folder music."
    )

if not os.path.exists(FONT):
    raise SystemExit("ERROR: Nedostaje font.")

random.shuffle(clips)
random.shuffle(music)

today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# 2. Napravi tri videa
for i in range(3):
    style = STYLES[i]
    clip = clips[i % len(clips)]
    track = music[i % len(music)]
    quote = random.choice(style["quotes"])

    output = f"videos/luxury_{today}_{i + 1}.mp4"
    text_file = f"videos/quote_{i + 1}.txt"

    with open(text_file, "w", encoding="utf-8") as file:
        file.write(quote)

    video_filter = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase,"
        f"crop={W}:{H},setsar=1,"
        "zoompan=z='min(zoom+0.0007,1.10)':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
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
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-stream_loop", "-1",
        "-i", clip,
        "-stream_loop", "-1",
        "-i", track,
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
        output,
    ]

    print(f"Pravim {style['name']} video: {output}")
    subprocess.run(command, check=True)
    print(f"USPESNO: {output}")

print("Luxury Life AI zavrsio!")
