"""
Step 10: YouTube Uploader
Uploads videos to YouTube as Shorts with metadata, thumbnail, and scheduling.
"""

import os
import pickle
import datetime
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import Config


# YouTube API scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]


class YouTubeUploader:
    """Uploads videos to YouTube with full metadata and thumbnail support."""

    def __init__(self):
        self.youtube = None

    def authenticate(self):
        """Authenticate with YouTube API using OAuth2.

        On first run, opens a browser for authorization.
        Subsequent runs use cached token.

        Returns:
            bool: True if authentication succeeded.
        """
        creds = None
        token_path = os.path.join(Config.BASE_DIR, "youtube_token.pickle")

        # Load cached token
        if os.path.exists(token_path):
            with open(token_path, "rb") as token_file:
                creds = pickle.load(token_file)

        # Refresh or get new token
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None

            if not creds:
                client_secret_path = os.path.join(
                    Config.BASE_DIR, Config.YOUTUBE_CLIENT_SECRET_FILE
                )
                if not os.path.exists(client_secret_path):
                    print(f"\n❌ YouTube client secret file not found: {client_secret_path}")
                    print("   Download it from Google Cloud Console > APIs > Credentials")
                    print("   Save as 'client_secret.json' in the project root.\n")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
                creds = flow.run_local_server(port=0, prompt="consent")

            # Save token for next time
            with open(token_path, "wb") as token_file:
                pickle.dump(creds, token_file)

        self.youtube = build("youtube", "v3", credentials=creds)
        return True

    def upload_video(self, video_path, metadata, thumbnail_path=None):
        """Upload a video to YouTube as a Short.

        Args:
            video_path: Path to the MP4 file.
            metadata: dict with 'title', 'description', 'tags'.
            thumbnail_path: Optional path to thumbnail PNG.

        Returns:
            dict: Upload result with video ID and URL.
        """
        if not self.youtube:
            if not self.authenticate():
                return {"error": "Authentication failed"}

        # Prepare video metadata
        body = {
            "snippet": {
                "title": metadata.get("title", "Funny Cartoon Short"),
                "description": metadata.get("description", "Comedy cartoon short"),
                "tags": metadata.get("tags", ["comedy", "shorts", "cartoon"]),
                "categoryId": Config.YOUTUBE_CATEGORY,
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en",
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": Config.MADE_FOR_KIDS,
                "embeddable": True,
                "publicStatsViewable": True,
            },
        }

        # Add scheduled publish time if properly configured
        # SCHEDULE_TIME must be a full ISO 8601 datetime in the future
        schedule_time = getattr(Config, 'SCHEDULE_TIME', None)
        if schedule_time:
            try:
                # Try to parse as full datetime (e.g. "2026-02-20T13:20:00Z")
                scheduled_dt = datetime.datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))
                if scheduled_dt > datetime.datetime.now(datetime.timezone.utc):
                    body["status"]["privacyStatus"] = "private"
                    body["status"]["publishAt"] = scheduled_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                    print(f"   📅 Scheduled for: {body['status']['publishAt']}")
                else:
                    print("   ℹ️  Schedule time is in the past, publishing immediately")
            except (ValueError, TypeError):
                # Not a valid full datetime — publish immediately
                pass

        # Upload video file
        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=10 * 1024 * 1024,  # 10MB chunks
        )

        print(f"\n📤 Uploading video: {metadata.get('title', 'Video')}...")

        request = self.youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"   Upload progress: {progress}%")

        video_id = response["id"]
        video_url = f"https://www.youtube.com/shorts/{video_id}"

        print(f"✅ Video uploaded! ID: {video_id}")
        print(f"🔗 URL: {video_url}")

        # Upload thumbnail
        if thumbnail_path and os.path.exists(thumbnail_path):
            self._set_thumbnail(video_id, thumbnail_path)

        # Add to playlist if configured
        if Config.PLAYLIST_ID:
            self._add_to_playlist(video_id)

        return {
            "video_id": video_id,
            "url": video_url,
            "title": metadata.get("title"),
        }

    def _set_thumbnail(self, video_id, thumbnail_path):
        """Set a custom thumbnail for the uploaded video.

        Args:
            video_id: YouTube video ID.
            thumbnail_path: Path to the thumbnail image.
        """
        try:
            media = MediaFileUpload(thumbnail_path, mimetype="image/png")
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=media,
            ).execute()
            print(f"🖼️  Thumbnail set successfully")
        except Exception as e:
            print(f"⚠️  Could not set thumbnail: {e}")
            print("   (Custom thumbnails require a verified YouTube account)")

    def _add_to_playlist(self, video_id):
        """Add the video to a playlist.

        Args:
            video_id: YouTube video ID.
        """
        try:
            self.youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": Config.PLAYLIST_ID,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id,
                        },
                    }
                },
            ).execute()
            print(f"📋 Added to playlist: {Config.PLAYLIST_ID}")
        except Exception as e:
            print(f"⚠️  Could not add to playlist: {e}")
