from pydantic import BaseModel

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