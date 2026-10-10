
import json
import random
import re
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
VIDEO_FOLDER = Path("videos")
STATE_FILE = Path("uploaded_videos.json")

# Razliciti naslovi i opisi za luksuzni lifestyle sadrzaj
IDEAS = [
    {
        "titles": [
            "The Luxury Lifestyle Most People Only Dream Of",
            "POV: You Finally Made It",
            "This Is What Success Looks Like",
            "Your Future Lifestyle Starts Today",
            "The Mindset Behind a Luxury Life",
        ],
        "description": (
            "Dream bigger. Work harder. Build a life on your own terms.\n\n"
            "Luxury is more than expensive cars and beautiful homes — "
            "it's freedom, discipline, and the ability to choose your path.\n\n"
            "Follow for more luxury lifestyle inspiration, dream cars, "
            "beautiful properties, and success mindset content.\n\n"
            "#Shorts #LuxuryLifestyle #Success #Motivation #DreamLife"
        ),
        "tags": ["luxury lifestyle", "success", "motivation", "dream life"],
    },
    {
        "titles": [
            "POV: Your Dream Car Is Finally Yours",
            "The Sound of Success",
            "Which Supercar Would You Choose?",
            "A Different Level of Luxury",
            "Supercar Dreams Hit Different",
        ],
        "description": (
            "Supercars, cinematic moments, and the dream of driving "
            "something extraordinary.\n\n"
            "Which car would you choose? Tell us in the comments.\n\n"
            "Follow for more supercars, luxury cars, automotive inspiration, "
            "and premium lifestyle videos.\n\n"
            "#Shorts #Supercars #LuxuryCars #Cars #CarLifestyle"
        ),
        "tags": ["supercars", "luxury cars", "dream car", "car lifestyle"],
    },
    {
        "titles": [
            "Imagine Waking Up in This Mansion",
            "A Home That Feels Like a Dream",
            "Inside the World of Luxury Living",
            "Would You Live Here?",
            "This View Is Worth Waking Up For",
        ],
        "description": (
            "Stunning homes, beautiful views, and inspiration for your "
            "dream lifestyle.\n\n"
            "Would you live in a place like this? Let us know below.\n\n"
            "Follow for more luxury homes, dream mansions, architecture, "
            "and lifestyle inspiration.\n\n"
            "#Shorts #LuxuryHomes #Mansion #Architecture #DreamHome"
        ),
        "tags": ["luxury homes", "mansions", "architecture", "dream home"],
    },
    {
        "titles": [
            "Quiet Luxury. Powerful Mindset.",
            "Success Speaks Without Words",
            "The Details Make the Difference",
            "Timeless Style, Different Level",
            "Luxury Is in the Details",
        ],
        "description": (
            "Timeless style, refined details, and a mindset focused on "
            "building something meaningful.\n\n"
            "Save this video for a little daily inspiration.\n\n"
            "Follow for more premium lifestyle, luxury watches, style, "
            "and success motivation.\n\n"
            "#Shorts #QuietLuxury #LuxuryStyle #Mindset #Lifestyle"
        ),
        "tags": ["quiet luxury", "luxury style", "watches", "mindset"],
    },
]


def load_uploaded():
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_uploaded(uploaded):
    STATE_FILE.write_text(
        json.dumps(uploaded, indent=2),
        encoding="utf-8",
    )


def choose_idea(filename):
    name = filename.lower()

    if any(word in name for word in ("car", "supercar", "auto")):
        pool = [IDEAS[1], IDEAS[0]]
    elif any(word in name for word in ("mansion", "home", "villa", "house")):
        pool = [IDEAS[2], IDEAS[0]]
    elif any(word in name for word in ("watch", "style", "premium")):
        pool = [IDEAS[3], IDEAS[0]]
    else:
        pool = IDEAS

    idea = random.choice(pool)
    title = random.choice(idea["titles"])

    # Add a unique, relevant suffix without exceeding YouTube's title limit.
    suffixes = ["#Shorts", " | Luxury Lifestyle", " #Luxury"]
    title = f"{title} {random.choice(suffixes)}"
    title = title[:100]

    return title, idea["description"], idea["tags"]


def main():
    token_file = Path("token.json")

    if not token_file.exists():
        raise FileNotFoundError("Nedostaje token.json")

    credentials = Credentials.from_authorized_user_file(
        str(token_file), SCOPES
    )
    youtube = build("youtube", "v3", credentials=credentials)

    videos = sorted(VIDEO_FOLDER.glob("*.mp4"))
    if not videos:
        raise FileNotFoundError("Nema MP4 videa u folderu videos/")

    uploaded = load_uploaded()
    success = 0

    for video in videos:
        if video.name in uploaded:
            print(f"Preskacem vec evidentiran video: {video.name}")
            continue

        title, description, tags = choose_idea(video.name)

        body = {
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags + ["shorts"],
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": "private",
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            str(video),
            mimetype="video/mp4",
            resumable=True,
        )

        try:
            response = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            ).execute()

            uploaded[video.name] = response["id"]
            save_uploaded(uploaded)
            success += 1

            print(
                f"Uspeh: {video.name} | Naslov: {title} | "
                f"YouTube ID: {response['id']}"
            )

        except HttpError as error:
            message = error.content.decode("utf-8", errors="replace")
            print(f"Upload nije uspeo za {video.name}: {error}")

            if "uploadLimitExceeded" in message or "quotaExceeded" in message:
                print("YouTube ogranicenje. Prekidam ostale pokusaje.")

            break

    print(f"Uspešno otpremljeno u ovom pokretanju: {success}")


if __name__ == "__main__":
    main()
