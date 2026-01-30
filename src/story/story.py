from google import genai
from google.genai import types
import dspy
from dotenv import load_dotenv
from schemas.schemas import StoryGenerationOutput
from typing import List
from consts.test_consts import STORY

load_dotenv()

dspy.configure(lm=dspy.LM("gemini/gemini-2.5-flash"), adapter=dspy.JSONAdapter())

class GenerateStory(dspy.Signature):
    """Generate a Reddit-like story post for a given topic. 
    The story should be detailed and engaging, taking approximately 1 minute to read (150-200 words).
    Include vivid descriptions, dialogue, and narrative tension to make it compelling."""
    
    topic: str = dspy.InputField()
    story: StoryGenerationOutput = dspy.OutputField(
        desc="A Reddit-style story with title, text (150-200 words minimum), TLDR and a short title."
             "The text should be a complete narrative arc with beginning, middle, and end."
    )

def generate_story(topic: str, test=False) -> StoryGenerationOutput:
    if test:
        return STORY
    
    # Enhanced prompt with explicit length requirements
    enhanced_topic = (
        f"{topic}\n\n"
        "Important: Write a detailed story that takes about 1 minute to read. "
        "Include specific details, dialogue, emotions, and a full narrative structure. "
        "Aim for 200-250 words in the main text."
    )
    
    predict = dspy.Predict(GenerateStory)
    return predict(topic=enhanced_topic).story

# print(generate_story(topic="New dorm"))