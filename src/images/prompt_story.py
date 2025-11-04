from google import genai
from google.genai import types

import dspy
import pydantic
from dotenv import load_dotenv

from schemas.schemas import ImagesPromptsOutput
from consts.test_consts import STORY_CHUNKED
from typing import List

load_dotenv()


STORY = """Before I adopted Buster, my evenings were quiet. I'd come home from work, make dinner, watch some TV, and maybe read a book. My apartment was always spotless, and my schedule was entirely my own. Then came Buster, a scruffy terrier mix with the biggest, most soulful eyes I'd ever seen. He was a rescue, a bit timid at first, but full of an energy I hadn't anticipated. Now, my evenings are a whirlwind. The moment I walk through the door, I'm greeted by a frantic tail wag and a happy bark. Dinner is often delayed because Buster needs his walk, his playtime, and his endless belly rubs. My apartment? Let's just say 'lived-in' is a generous description, with dog toys scattered like confetti and a fine layer of fur on everything. My schedule revolves around his potty breaks, his feeding times, and ensuring he gets enough exercise. I've learned to appreciate early morning walks, even in the rain, and I've discovered a whole community of dog owners at the local park. There are days I'm exhausted, covered in mud, or frustrated by a chewed-up shoe. But then he'll rest his head on my lap, let out a contented sigh, and look up at me with those big, loving eyes, and I remember why I wouldn't trade this chaotic, fur-filled life for anything. He's not just a pet; he's family, a constant source of joy, laughter, and unconditional love. My life is undeniably messier, but it's also infinitely richer."""


dspy.configure(lm=dspy.LM("gemini/gemini-2.5-flash"), adapter=dspy.JSONAdapter())



class StoryImagesPrompts(dspy.Signature):
    """Divide Story into equal chunks and provide images prompts"""
    full_post_text: str = dspy.InputField()
    story: list[ImagesPromptsOutput] = dspy.OutputField(desc="Story divided in chunks, with text fragment and image generating prompt.")


def generate_images_prompts(full_post_text: str, test=False) -> List[ImagesPromptsOutput]:

    if test:
        return STORY_CHUNKED

    predict = dspy.Predict(StoryImagesPrompts)
    return predict(full_post_text=full_post_text).story


print(generate_images_prompts(full_post_text=STORY))