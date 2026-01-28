from typing import List
from pathlib import Path
from schemas.schemas import Video

from tiktok_uploader.upload import upload_videos
from tiktok_uploader.auth import AuthBackend

COOKIES_PATH = Path(__file__).resolve().parent.parent.parent / Path("cookies.txt")
print(COOKIES_PATH)


class Uploader:

    def __init__(self, videos: List[Video]):
        self.videos = videos

    def upload_tiktok(self, cookies: Path):

        auth = AuthBackend(cookies=cookies)
        videos = [v.model_dump(mode="json") for v in self.videos]
        
        failed_videos = upload_videos(videos=videos, auth=auth)

        for video in failed_videos:  # each input video object which failed
            print(f"{video['video']} with description {video['description']} failed")


if __name__ == "__main__":
    VIDEO_PATH = Path("/Users/szymon/Documents/projekciki/Content_Generation/src/data/videos/my_first_year_of_studying/my_first_year_of_studying.mp4")
    up = Uploader(videos=[Video(video=str(VIDEO_PATH), description="some description")])

    up.upload_tiktok(cookies=str(COOKIES_PATH))