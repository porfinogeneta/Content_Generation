from google import genai
from google.genai import types

import dspy
import pydantic
from dotenv import load_dotenv
import time
from tqdm import tqdm
import re
from typing import List

from schemas.schemas import ImagesPromptsOutput
from consts.test_consts import STORY_CHUNKED
from typing import List


load_dotenv()


STORY = """Okay, Reddit, I officially survived my first year of university, and honestly, I'm not sure if I should be celebrating or just collapsing into a coma. Coming straight out of high school, I thought I was prepared. I had good grades, I was organized, I even knew how to do my own laundry (mostly). Boy, was I wrong.\n\nThe first semester was a blur of orientation events, trying to figure out the campus map without looking like a lost puppy, and attempting to make friends in a sea of thousands of new faces. Lectures were overwhelming – suddenly, professors weren't just teaching; they were *expecting* you to understand complex theories in an hour. My first essay deadline hit me like a truck. I pulled an all-nighter, fueled by instant coffee and sheer panic, and submitted something I was only 50% sure made sense. The grade wasn't great, but it was a wake-up call.\n\nSecond semester was a different beast. I thought I had the hang of it, but then the real grind began. Group projects became a test of patience and diplomacy. I learned that 'group work' often means 'one person does 80% of the work while others contribute memes.' There were moments of pure despair, like staring at a textbook at 3 AM, convinced I understood absolutely nothing, or getting a midterm back that made me question all my life choices. Imposter syndrome was a constant companion.\n\nBut it wasn't all doom and gloom. I found my people – a small group of friends who understood the struggle, shared notes, and were always down for a late-night snack run. I discovered a passion for a subject I never expected to love. I learned to cook (badly, but still). I figured out how to manage my time (mostly). I even started enjoying the challenge of some of the more difficult concepts.\n\nLooking back, it was a rollercoaster. I cried, I laughed, I probably aged five years. But I also grew so much. I'm more independent, more resilient, and I actually feel like I'm capable of tackling bigger things. To all the incoming freshmen: you got this. It's tough, but it's worth it. And for those who've been there, done that: what were your craziest first-year stories?"""

# dspy.configure(lm=dspy.LM("gemini/gemini-2.5-flash"), adapter=dspy.JSONAdapter())



# class StoryImagesPrompts(dspy.Signature):
#     full_story_text: str = dspy.InputField()
#     story: List[ImagesPromptsOutput] = dspy.OutputField(
#         instructions="""Break the story into VERY SMALL chunks - aim for 15-30 chunks minimum for a story of this length.
        
#         Create a new chunk (and image prompt) for EACH of these moments:
#         - Every time a new location or setting is introduced or changes
#         - Every time a character performs a distinct action or gesture
#         - Every time there's a change in what's being looked at or focused on
#         - Every emotional beat or reaction
#         - Every object mentioned that could be visualized
#         - Every transition in the narrative flow
        
#         Guidelines for chunking:
#         - A single sentence can and SHOULD produce 2-5 image prompts if it contains multiple visual elements
#         - Don't combine multiple actions into one chunk - split them up
#         - Even subtle changes (like a character's expression changing) deserve their own image
#         - Each chunk should represent ONE clear visual moment, not a sequence
        
#         For each image prompt:
#         - Describe the exact scene composition, camera angle, and focus
#         - Include consistent character descriptions (Mr. Henderson: elderly landlord, professional appearance)
#         - Maintain consistent visual style across all prompts (cinematic, realistic photography style)
#         - Be specific about lighting, mood, and atmosphere
#         - Include enough detail that each image will be visually distinct from the previous one
        
#         Example: Instead of one chunk for "He was tapping on the wall and found a hollow spot", 
#         create THREE chunks:
#         1. Mr. Henderson tapping methodically on the closet wall with his knuckles
#         2. Close-up of his hand stopping on a specific spot, pressing harder
#         3. His face showing surprise as he hears the hollow sound"""
#     )

# class StoryBreakdown(dspy.Signature):
#     """Break story into individual visual moments."""
#     full_story_text: str = dspy.InputField()
#     visual_moments: List[str] = dspy.OutputField(
#         instructions="Extract every single visual moment. Each action, reaction, object mention, or scene change should be its own item. Aim for 20-40 moments minimum."
#     )

# class MomentToPrompt(dspy.Signature):
#     """Convert a visual moment into a detailed image generation prompt."""
#     moment: str = dspy.InputField()
#     full_context: str = dspy.InputField()
#     image_prompt: str = dspy.OutputField(
#         instructions="Create a detailed, cinematic image generation prompt with specific composition, lighting, and style details."
#     )



# def generate_images_prompts(full_story_text: str, test=False) -> List[ImagesPromptsOutput]:

#     # if test:
#     #     return STORY_CHUNKED

#     # predict = dspy.Predict(StoryImagesPrompts)
#     # return predict(full_story_text=full_story_text).story
#     # Step 1: Break into moments
#     breakdown = dspy.Predict(StoryBreakdown)
#     moments = breakdown(full_story_text=full_story_text).visual_moments
    
#     print(f"Found {len(moments)} visual moments")
    
#     # Step 2: Convert each moment to a prompt
#     converter = dspy.Predict(MomentToPrompt)
#     prompts = []
#     for moment in moments:
#         prompt = converter(moment=moment, full_context=full_story_text).image_prompt
#         prompts.append(prompt)
    
#     return prompts


# st = generate_images_prompts(full_story_text=STORY)
# print(len(st))
# print(st[0])




def chunk_story_rules_based(full_story_text: str) -> List[str]:
    """
        Break story into visual moments using rules.
        For now only 2 senteces are moments, probably this could be replaced
        with some LLM approach.
    """
    
    # Split into sentences
    sentences = [m.group().strip() for m in re.finditer(r'[^.?!]*[,.?!]', full_story_text)]
    moments = []

    # if there is too many sentences, we merge them
    while len(sentences) > 20:
        h = []
        for i in range(0, len(sentences) - 1, 2):
            h.append(sentences[i] + " " + sentences[i+1])
        sentences = h
    
    moments = sentences
    # for sentence in sentences:
    #     if len(sentence.split()) > 30:
    #         sub_moments = [m.group() for m in re.finditer(r'[^,]*,|[^,]+', sentence)]
    #         moments += sub_moments
    #     else:
    #         moments.append(sentence)
    
    return moments

def batch_list(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]

class MomentsToPrompts(dspy.Signature):
    """Convert multiple visual moments into detailed image generation prompts in batch."""
    moments: list[str] = dspy.InputField(desc="List of visual moments to convert")
    full_context: str = dspy.InputField(desc="Full story text for context")
    image_prompts: list[str] = dspy.OutputField(
        desc="List of detailed, cinematic image generation prompts with specific composition, lighting, and style details. Must be in the same order as input moments."
    )


def generate_images_prompts(full_story_text: str, batch_size=7, test=False) -> List[ImagesPromptsOutput]:
    if test:
        return STORY_CHUNKED
    
    moments = chunk_story_rules_based(full_story_text)
    # moments = [full_story_text]
    # print(f"Generated {len(moments)} moments via rules")
    # print(len(moments))
    # Configure model
    # dspy.configure(lm=dspy.LM("gemini/gemini-2.5-flash"))
    converter = dspy.Predict(MomentsToPrompts)


    outputs = []

    for i in range(0, len(moments), batch_size):
        # use batched moments
        batch = moments[i:i+batch_size]
        # Single API call for all moments
        result = converter(
            moments=batch,
            full_context=full_story_text
        )

        # print(result)

        # Fallback logic if lengths mismatch
        if len(result.image_prompts) != len(batch):
            print("Warning: Length mismatch in batch, padding or truncating...")

    
        # Combine moments with their prompts
        for moment, img_prompt in zip(batch, result.image_prompts):
            outputs.append(
                ImagesPromptsOutput(
                    text=moment,
                    img_prompt=img_prompt
                )
            )
    
    return outputs

# st = generate_images_prompts(full_story_text=STORY)
# print(len(st))
# print(st[0])