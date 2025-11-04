

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from typing import List, Tuple
import concurrent.futures


from story.story import generate_story
from schemas.schemas import StoryGenerationOutput, ImagesPromptsOutput
from images.prompt_story import generate_images_prompts
from images.images import generate_image


# Graph state
class GraphState(TypedDict):
    post: StoryGenerationOutput
    images_prompts: List [ImagesPromptsOutput]
    photos_links: List[str]
    audio_link: str
    


def generate_story_node(state: GraphState) -> dict:
    print("---NODE: Generating Story---")
    return {"post": generate_story(topic="Having a dog")}

def generate_image_prompts_node(state: GraphState) -> dict:
    print("---NODE: Generating prompts for images---")
    post = state["post"]
    return generate_images_prompts(full_post_text=post)

def generate_images_node(state: GraphState) -> dict:
    print("---NODE: Generating Images & Saving in the cloud---")
    images_prompts: List[str] = state["images_prompts"]

    photos: List[Tuple[int,str]] = []

    MAX_WORKERS = 5

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        
        # mapping future objects to index
        future_to_index = {
            # resubmission probably should be on the generate_image side
            executor.submit(generate_image, prompt=prompt): i 
            for i, prompt in enumerate(images_prompts)
        }

        for future in concurrent.futures.as_completed(future_to_index):
            i = future_to_index[future]
            
            try:
                # wait for the thread to complete, return a value
                url = future.result()
                photos.append((i, url))
            except Exception as exc:
                prompt = images_prompts[i]
                print(f"Image generation for prompt #{i} failed: {exc}. Prompt: '{prompt}'")

    # # at first all are failed
    # failed_generations = [(i,prompt) for i, prompt in enumerate(images_prompts)]
    
    # while failed_generations:
    #     i,prompt = failed_generations.pop()
    #     try:
    #         url = generate_image(prompt=prompt)
    #         photos.append((i,url))
    #     except:
    #         failed_generations.push((i,prompt))

    # sort photos to make sense chronologically
    photos.sort(key=lambda item: item[0])
    return {"photos_links" : [url for _,url in photos]}



def generate_audio_node(state: StateGraph) -> dict:
    print("---NODE: Generating Audio---")


# workflow = StateGraph(State)


def __init__():
    generate_story_node(state = None)

