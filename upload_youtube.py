
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
    "models/gemini-3.5-flash-lite:generateContent"
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

    quote_files = sorted(VIDEO_FOLDER.glob("quote_*.txt"))

    if quote_files:
        try:
            quote = quote_files[0].read_text(
                encoding="utf-8"
            ).strip()

            if quote:
                context += f"\nMotivational text: {quote}"
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

    fallback_tags = [
        "luxury lifestyle",
        "motivation",
        "success",
    ]

    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY nedostaje.")
        return fallback_title, fallback_description, fallback_tags

    prompt = f"""
Create original YouTube Shorts metadata for a luxury lifestyle channel.

Use the supplied information to produce:
1. One catchy English title, maximum 90 characters.
2. A natural English description of 2-4 short paragraphs.
3. Five to eight relevant hashtags.
4. Five to eight relevant YouTube tags.

Be specific to the supplied information. Avoid fake facts,
misleading claims, and repetitive clickbait.
Do not pretend to have watched the video.

Context:
{get_video_context(video)}

Return only valid JSON:
{{
  "title": "Catchy title",
  "description": "Useful video description",
  "hashtags": ["#Shorts", "#LuxuryLifestyle"],
  "tags": ["luxury lifestyle", "motivation"]
}}
"""

    try:
        response = requests.post(
            GEMINI_URL,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY,
            },
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

        if not response.ok:
            print(
                f"Gemini HTTP {response.status_code}: "
                f"{response.text[:1000]}"
            )
            return fallback_title, fallback_description, fallback_tags

        result = response.json()
        generated_text = (
            result["candidates"][0]["content"]["parts"][0]["text"]
        )
        data = json.loads(generated_text)

        title = str(data.get("title", fallback_title)).strip()[:100]
        description = str(
            data.get("description", fallback_description)
        ).strip()[:4500]

        hashtags = data.get(
            "hashtags",
            ["#Shorts", "#LuxuryLifestyle"],
        )
        tags = data.get(
            "tags",
            ["luxury lifestyle", "motivation"],
        )

        if not isinstance(hashtags, list):
            hashtags = ["#Shorts", "#LuxuryLifestyle"]

        if not isinstance(tags, list):
            tags = ["luxury lifestyle", "motivation"]

        clean_hashtags = []
        for item in hashtags[:8]:
            tag = str(item).strip()
            if tag and tag not in clean_hashtags:
                clean_hashtags.append(tag)

        for required in ["#Shorts", "#LuxuryLifestyle"]:
            if required.lower() not in [
                item.lower() for item in clean_hashtags
            ]:
                clean_hashtags.append(required)

        description += "\n\n" + " ".join(clean_hashtags[:10])

        clean_tags = [
            str(item).strip()[:100]
            for item in tags[:15]
            if str(item).strip()
        ]

        print(f"AI naslov: {title}")
        print("Gemini je napravio opis i hashtagove.")

        return title, description, clean_tags or fallback_tags

    except (
        requests.RequestException,
        KeyError,
        IndexError,
        TypeError,
        ValueError,
    ) as error:
        print(f"Gemini greska: {error}")
        return fallback_title, fallback_description, fallback_tags


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
            result = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            ).execute()

            uploaded[video.name] = result["id"]
            save_uploaded(uploaded)
            success += 1

            print(
                f"Upload uspesan: {video.name} | "
                f"YouTube ID: {result['id']}"
            )

        except HttpError as error:
            message = error.content.decode(
                "utf-8", errors="replace"
            )
            print(f"YouTube greska: {message}")

            if "uploadLimitExceeded" in message:
                print(
                    "YouTube limit je dostignut. "
                    "Sacekaj pre sledeceg pokusaja."
                )

            break

    print(f"U ovom pokretanju uploadovano: {success}")


if __name__ == "__main__":
    main()
