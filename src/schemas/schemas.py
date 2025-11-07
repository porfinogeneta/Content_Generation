from pydantic import BaseModel
from typing import List
from pathlib import Path



# STORY
class StoryGenerationOutput(BaseModel):
    title: str
    text: str
    tldr: str

# IMAGES

class ImagesPromptsOutput(BaseModel):
    text: str
    img_prompt: str


# AUDIO

# GRAPH STATE
class GraphState(BaseModel):
    topic: str
    test: bool
    story: StoryGenerationOutput | None
    image_prompts: List [ImagesPromptsOutput] | None
    photo_links: List[str] | None
    audio_link: Path | None