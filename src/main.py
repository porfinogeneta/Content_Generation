from pipeline.pipeline import Pipeline
from video.editor import Editor
import json
from pathlib import Path


ROOT_SRC = Path(__file__).resolve().parent
INPUT_DATA_PATH = ROOT_SRC / "data" / "final_states"
DATA_PATH = ROOT_SRC / "data"

if __name__ == "__main__":
    # come up with the topic
    topic = "Beautiful friendship story"
    topic_slug = topic.lower().replace(" ", "_")
    
    # 1. run pipeline, and create a state
    pipeline = Pipeline(topic=topic, story_slug=topic_slug, test=False)
    pipeline.workflow_compile_and_run()
    
    # 2. run editor, and save the movie
    INPUT_DICT_PATH = INPUT_DATA_PATH / pipeline.story_slug / Path(f"{topic_slug}.json")
    movie_data = None

    try:
        with open(INPUT_DICT_PATH, 'r') as json_file:
            movie_data = json.load(json_file)
    except:
        raise Exception("file")
    

    editor = Editor(topic=topic,
                    story_slug=topic_slug,
                    playback_speed=1.5,
                    scenes=movie_data["image_prompts"],
                    audio_urls=movie_data["audio_links"],
                    image_urls=movie_data["photo_links"])
    
    editor.create_video()