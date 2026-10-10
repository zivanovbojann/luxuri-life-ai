
import json
import os
import random
from pathlib import Path

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

VIDEO_FOLDER = Path("videos")
STATE_FILE = Path("uploaded_videos.json")
TOKEN_FILE = Path("token.json")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    "models/gemini-2.5-flash:generateContent"
)

FALLBACK_TITLES = [
    "The Luxury Lifestyle Most People Dream Of",
    "POV: You Finally Made It",
    "Which Dream Car Would You Choose?",
    "Imagine Living in This Mansion",
    "Quiet Luxury. Powerful Mindset.",
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


def get_video_context(video):
    context = f"Video filename: {video.name}"

    quote_files = sorted(
        VIDEO_FOLDER.glob("quote_*.txt")
    )

    if quote_files:
        try:
            quote = quote_files[0].read_text(
                encoding="utf-8"
            ).strip()

            if quote:
                context += f"\nText or motivational quote: {quote}"
        except OSError:
            pass

    return context


def generate_metadata(video):
    fallback_title = random.choice(FALLBACK_TITLES)

    fallback_description = (
        "Luxury lifestyle, dream cars, beautiful homes, "
        "and daily motivation.\n\n"
        "What does your dream lifestyle look like? "
        "Share your thoughts in the comments.\n\n"
        "#Shorts #LuxuryLifestyle #Motivation #Success"
    )

    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY nije pronadjen. Koristim rezervni tekst.")
        return fallback_title, fallback_description, [
            "luxury lifestyle", "motivation", "success"
        ]

    prompt = f"""
You create original YouTube Shorts metadata for a luxury
lifestyle channel.

Use the context below to create:
- One catchy, natural English title, maximum 90 characters.
- A unique, useful English description of 2-4 short paragraphs.
- 5-8 relevant hashtags.
- 5-8 relevant YouTube tags.

Make the title specific to the available context.
Avoid misleading claims, fake facts, keyword stuffing,
and repetitive clickbait.
Do not claim to have seen details that are not provided.

Context:
{get_video_context(video)}

Return ONLY valid JSON in this exact format:
{{
  "title": "Your title",
  "description": "Your description",
  "hashtags": ["#Shorts", "#LuxuryLifestyle"],
  "tags": ["luxury lifestyle", "motivation"]
}}
"""

    try:
        response = requests.post(
            GEMINI_URL,
            params={"key": GEMINI_API_KEY},
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.8,
                    "responseMimeType": "application/json",
                },
            },
            timeout=45,
        )

        response.raise_for_status()
        result = response.json()

        text = result["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(text)

        title = str(data.get("title", fallback_title)).strip()
        description = str(data.get("description", fallback_description)).strip()
        hashtags = data.get("hashtags", ["#Shorts", "#LuxuryLifestyle"])
        tags = data.get("tags", ["luxury lifestyle", "motivation"])

        if not isinstance(hashtags, list):
            hashtags = ["#Shorts", "#LuxuryLifestyle"]

        if not isinstance(tags, list):
            tags = ["luxury lifestyle", "motivation"]

        title = title[:100]
        description = description[:4900]
        hashtags = [str(x).strip() for x in hashtags[:8]]
        tags = [str(x).strip() for x in tags[:15]]

        for hashtag in ["#Shorts", "#LuxuryLifestyle"]:
            if hashtag.lower() not in [x.lower() for x in hashtags]:
                hashtags.append(hashtag)

        description += "\n\n" + " ".join(hashtags[:10])

        tags = [tag[:100] for tag in tags if tag.strip()]

        print(f"AI naslov: {title}")
        return title, description, tags

    except (
        requests.RequestException,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
    ) as error:
        print(f"Gemini nije uspeo da napravi opis: {error}")
        print("Koristim rezervni naslov i opis.")

        return fallback_title, fallback_description, [
            "luxury lifestyle", "motivation", "success"
        ]


def main():
    if not TOKEN_FILE.exists():
        raise FileNotFoundError("Nedostaje token.json")

    credentials = Credentials.from_authorized_user_file(
        str(TOKEN_FILE),
        ["https://www.googleapis.com/auth/youtube.upload"],
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

        title, description, tags = generate_metadata(video)

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
                f"Upload uspesan: {video.name} | "
                f"YouTube ID: {response['id']}"
            )

        except HttpError as error:
            message = error.content.decode(
                "utf-8", errors="replace"
            )
            print(f"YouTube upload greska: {message}")

            if "uploadLimitExceeded" in message or "quotaExceeded" in message:
                print("YouTube limit je dostignut. Prekidam upload.")
            break

    print(f"U ovom pokretanju uploadovano: {success}")


if __name__ == "__main__":
    main()
