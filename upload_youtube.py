
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
VIDEO_FOLDER = Path("videos")


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

    uploaded = 0
    failed = 0

    for video in videos:
        print(f"Pokušavam upload: {video.name}")

        body = {
            "snippet": {
                "title": f"{video.stem} #Shorts"[:100],
                "description": (
                    "Daily luxury lifestyle inspiration. #Shorts"
                ),
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
            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            )

            response = request.execute()

            uploaded += 1
            print(
                f"USPEH: {video.name} | "
                f"YouTube ID: {response['id']}"
            )

        except HttpError as error:
            failed += 1
            error_text = error.content.decode(
                "utf-8", errors="replace"
            )

            if (
                "uploadLimitExceeded" in error_text
                or "quotaExceeded" in error_text
            ):
                print(
                    "YouTube je dostigao ograničenje za upload. "
                    "Prekidam ostale pokušaje."
                )
                break

            print(f"GREŠKA za {video.name}: {error}")
            break

    print(f"Završeno. Uspešno: {uploaded}; greške: {failed}.")


if __name__ == "__main__":
    main()
