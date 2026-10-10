
import json
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
VIDEO_FOLDER = Path("videos")
STATE_FILE = Path("uploaded_videos.json")


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
            print(f"Preskačem već evidentiran video: {video.name}")
            continue

        body = {
            "snippet": {
                "title": f"{video.stem} #Shorts"[:100],
                "description": "Daily luxury lifestyle inspiration. #Shorts",
                "tags": ["shorts", "luxury", "lifestyle"],
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
                f"Uspešan upload: {video.name} "
                f"| YouTube ID: {response['id']}"
            )

        except HttpError as error:
            message = error.content.decode("utf-8", errors="replace")
            print(f"Upload nije uspeo za {video.name}: {error}")

            if "uploadLimitExceeded" in message or "quotaExceeded" in message:
                print("Ograničenje YouTube-a. Prekidam ostale pokušaje.")
                break

            break

    print(f"Uspešno otpremljeno u ovom pokretanju: {success}")


if __name__ == "__main__":
    main()
