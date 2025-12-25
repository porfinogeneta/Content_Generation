from pipeline.pipeline import Pipeline
from video.editor import Editor
import json
from pathlib import Path


ROOT_SRC = Path(__file__).resolve().parent
INPUT_DATA_PATH = ROOT_SRC / "data" / "final_states"
DATA_PATH = ROOT_SRC / "data"

if __name__ == "__main__":
    # will be like
    # 1. run pipeline
    title = "First year of studies"
    pipeline = Pipeline(title, test=True)
    pipeline.workflow_compile_and_run()
    # 2. run editor

    INPUT_DICT_PATH = INPUT_DATA_PATH / pipeline.story_slug / Path(f"{title}.json")
    movie_data = None

    try:
        with open(INPUT_DICT_PATH, 'r') as json_file:
            movie_data = json.load(json_file)
    except:
        raise Exception("file")
    
    TITLE = movie_data.get("title", None)

    editor = Editor(title=TITLE,
                    playback_speed=1.5,
                    scenes=movie_data["image_prompts"],
                    audio_url=movie_data["audio_link"],
                    image_urls=movie_data["photo_links"])
    
    editor.create_video()


    # 3. upload video (for now has to be manual)
    # class YouTubeAPI:

    #     def upload_video(self, file_path, title, description, category_id, privacy_status='private'):
    #         body = {
    #             'snippet': {
    #                 'title': title,
    #                 'description': description,
    #                 'categoryId': category_id
    #             },
    #             'status': {
    #                 'privacyStatus': privacy_status
    #             }
    #         }

    #         media = MediaFileUpload(file_path, resumable=True)

    #         request = self.youtube.videos().insert(
    #             part='snippet,status',
    #             body=body,
    #             media_body=media
    #         )

    #         response = request.execute()
    #         return response
