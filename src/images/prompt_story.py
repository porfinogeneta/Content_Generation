from google import genai
from google.genai import types

import dspy
import pydantic
from dotenv import load_dotenv

from schemas.schemas import ImagesPromptsOutput
from consts.test_consts import STORY_CHUNKED
from typing import List

load_dotenv()


STORY = """So, I just moved into this charming, albeit slightly creaky, old apartment building downtown. It's got character, you know? High ceilings, original hardwood, and a landlord, Mr. Henderson, who's been managing properties in this city for what feels like a century. He's a stickler for details, which I appreciate, but it also meant our move-in inspection was going to be *thorough*. And I mean *thorough*.\n\nWe started in the living room, documenting every tiny scuff, every paint chip, every slightly loose floorboard. He had a clipboard, a flashlight, and a magnifying glass, no joke. We moved into the master bedroom, which had this rather large, built-in bookshelf in the closet. It looked old, probably original to the building, and a bit rickety, but functional.\n\nMr. Henderson was meticulously checking the back wall of the closet, behind the bookshelf. He was tapping, listening, making notes about the plaster. Suddenly, he stopped. He tapped again, a bit harder, on a specific spot. It sounded distinctly hollow. He frowned, then pushed gently. Nothing. He pushed a bit harder, and to both our astonishment, a faint, almost invisible seam appeared in the wall, running vertically and horizontally.\n\nHis eyes widened. \"Well, I'll be,\" he muttered, completely taken aback. He tried to pry it open, but it was stuck. I offered to help, and together, we managed to get a grip on the edge. With a collective grunt, a section of the wall, about three feet wide and five feet tall, swung inward with a soft creak, revealing a small, dark, dusty, empty room. It was barely big enough for one person to stand in, maybe 4x4 feet, and completely bare except for a thick layer of dust and cobwebs.\n\nWe both just stood there, staring into the void. Mr. Henderson, who had owned and managed this building for over twenty years, was absolutely speechless. \"I... I had no idea,\" he finally stammered, his flashlight beam dancing around the tiny space. \"Never in all my years. This is... incredible!\" We found nothing but a single, very old, empty wooden box in the corner, but the sheer surprise of it was enough. He was so excited, he almost forgot to finish the rest of the inspection. He even joked that it was a 'bonus feature' of the apartment. I'm still trying to figure out what it was used for, but it definitely made for the most interesting move-in inspection of my life."""

dspy.configure(lm=dspy.LM("gemini/gemini-2.5-flash"), adapter=dspy.JSONAdapter())



class StoryImagesPrompts(dspy.Signature):
    full_story_text: str = dspy.InputField()
    story: List[ImagesPromptsOutput] = dspy.OutputField(instructions="Divide the story into smallest possible chunks. " \
    "Make the division dynamic, meaning sentence could be divided into multiple chunks." \
    "For each chunk create a prompt that will create a photo using the same styling")


def generate_images_prompts(full_story_text: str, test=False) -> List[ImagesPromptsOutput]:

    if test:
        return STORY_CHUNKED

    predict = dspy.Predict(StoryImagesPrompts)
    return predict(full_story_text=full_story_text).story


# print(generate_images_prompts(full_story_text=STORY))