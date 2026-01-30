from pathlib import Path
from typing import List
import time
from schemas.schemas import Video
from tiktok_uploader.upload import upload_videos
from tiktok_uploader.auth import AuthBackend

COOKIES_PATH = Path(__file__).resolve().parent.parent.parent / Path("cookies.txt")

class Uploader:
    def __init__(self, videos: List[Video]):
        self.videos = videos
    
    def upload_tiktok(self, cookies: Path, max_retries: int = 3):
        auth = AuthBackend(cookies=cookies)
        videos = [v.model_dump(mode="json") for v in self.videos]
        
        for attempt in range(max_retries):
            try:
                print(f"Upload attempt {attempt + 1}/{max_retries}")
                failed_videos = upload_videos(
                    videos=videos, 
                    auth=auth, 
                    headless=False
                )
                
                if not failed_videos:
                    print("All videos uploaded successfully!")
                    return []
                
                # If some failed, retry only those
                videos = failed_videos
                
                for video in failed_videos:
                    print(f"{video['video']} with description {video['description']} failed")
                
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 5
                    print(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                print(f"Error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                else:
                    raise
        
        return failed_videos

if __name__ == "__main__":
    VIDEO_PATH = Path("/Users/szymon/Documents/projekciki/Content_Generation/src/data/videos/my_first_year_of_studying/my_first_year_of_studying.mp4")
    up = Uploader(videos=[Video(video=str(VIDEO_PATH), description="some description")])
    up.upload_tiktok(cookies=str(COOKIES_PATH))