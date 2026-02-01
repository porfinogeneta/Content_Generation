from pipeline.pipeline import Pipeline
from video.editor import Editor
import json
from pathlib import Path
import os


ROOT_SRC = Path(__file__).resolve().parent
INPUT_DATA_PATH = ROOT_SRC / "data" / "final_states"
DATA_PATH = ROOT_SRC / "data"

if __name__ == "__main__":
    # # come up with the topic
    topic = os.getenv("TOPIC", "Beautiful friendship story")
    topic_slug = topic.lower().replace(" ", "_")
    playback_speed = float(os.getenv("PLAYBACK_SPEED", "1.5"))
    test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    
    # 1. run pipeline, and create a state
    if not test_mode:
        print(f"Starting pipeline for topic: {topic}")
        pipeline = Pipeline(topic=topic, story_slug=topic_slug, test=test_mode)
        pipeline.workflow_compile_and_run()
        INPUT_DICT_PATH = INPUT_DATA_PATH / pipeline.story_slug / Path(f"{topic_slug}.json")
    else:
        INPUT_DICT_PATH = INPUT_DATA_PATH / "beautiful_friendship_story_test" / Path(f"beautiful_friendship_story_test.json")
    
    movie_data = None

    # 2. run editor, and save the movie
    try:
        with open(INPUT_DICT_PATH, 'r') as json_file:
            movie_data = json.load(json_file)
    except:
        raise Exception("file")
    

    editor = Editor(topic=topic,
                    story_slug=topic_slug,
                    playback_speed=playback_speed,
                    scenes=movie_data["image_prompts"],
                    audio_urls=movie_data["audio_links"],
                    image_urls=movie_data["photo_links"])
    
    
    output_path = editor.create_video()
    print(f"Video created successfully at: {output_path}")