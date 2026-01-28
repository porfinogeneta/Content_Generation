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

class PromptToReadOutput(BaseModel):
    text: str


# AUDIO

# GRAPH STATE
class GraphState(BaseModel):
    topic: str
    story_slug: str
    test: bool
    story: StoryGenerationOutput | None
    image_prompts: List [ImagesPromptsOutput] | None
    prompts_to_read: List[PromptToReadOutput] | None
    photo_links: List[str] | None
    audio_links: List[str] | None


# UPLOADING
class Video(BaseModel):
    video: Path
    description: str 