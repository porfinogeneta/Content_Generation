from google import genai
from google.genai import types

import dspy
from dotenv import load_dotenv
from schemas.schemas import StoryGenerationOutput
from typing import List
from consts.test_consts import STORY

load_dotenv()

# # The client gets the API key from the environment variable `GEMINI_API_KEY`.
# client = genai.Client()

# response = client.models.generate_content(
#     model="gemini-2.5-flash",
#     contents="Write me a 500 words Reddit-like post.",
#     config=types.GenerateContentConfig(
#         system_instruction="You are a psssionate Reddit user, reading every post there is.")
# )
# print(response.text)


dspy.configure(lm=dspy.LM("gemini/gemini-2.5-flash"), adapter=dspy.JSONAdapter())



class GenerateStory(dspy.Signature):
    """Generate a Reddit-like story post for a given topic."""
    topic: str = dspy.InputField()
    story: list[StoryGenerationOutput] = dspy.OutputField(desc="A Reddit-style story with title, text, and TLDR")


def generate_story(topic: str, test=False) -> StoryGenerationOutput:

    if test:
        return STORY

    predict = dspy.Predict(GenerateStory)
    return predict(topic=topic).story[0]

# print(generate_story())