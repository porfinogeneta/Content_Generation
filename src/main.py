

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from typing import List, Tuple
import concurrent.futures
from pathlib import Path
import uuid
from langgraph.checkpoint.memory import InMemorySaver

from story.story import generate_story
from schemas.schemas import ImagesPromptsOutput, GraphState
from images.prompt_story import generate_images_prompts
from images.images import generate_image
from audio.audio import generate_audio




def generate_story_node(state: GraphState) -> dict:
    print("---NODE: Generating Story---")
    return {"story": generate_story(topic=state.topic, test=state.test)}

def generate_image_prompts_node(state: GraphState) -> dict:
    print("---NODE: Generating prompts for images---")
    story = state.story
    return {"image_prompts": generate_images_prompts(full_story_text=story, test=state.test)}

def generate_images_node(state: GraphState) -> dict:
    print("---NODE: Generating Images & Saving in the cloud---")
    images_prompts_output: List[ImagesPromptsOutput] = state.image_prompts

    prompts = [output.img_prompt for output in images_prompts_output]

    photos: List[Tuple[int,str]] = []

    MAX_WORKERS = 5

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        
        # mapping future objects to index
        future_to_index = {
            # resubmission probably should be on the generate_image side
            executor.submit(generate_image, prompt=prompt, test=state.test): i 
            for i, prompt in enumerate(prompts)
        }

        for future in concurrent.futures.as_completed(future_to_index):
            i = future_to_index[future]
            
            try:
                # wait for the thread to complete, return a value
                url = future.result()
                photos.append((i, url))
            except Exception as exc:
                prompt = prompts[i]
                # photos.append("ERROR")
                print(f"Image generation for prompt #{i} failed: {exc}. Prompt: '{prompt}'")

    # # at first all are failed
    # failed_generations = [(i,prompt) for i, prompt in enumerate(image_prompts)]
    
    # while failed_generations:
    #     i,prompt = failed_generations.pop()
    #     try:
    #         url = generate_image(prompt=prompt)
    #         photos.append((i,url))
    #     except:
    #         failed_generations.push((i,prompt))

    # sort photos to make sense chronologically
    photos.sort(key=lambda item: item[0])
    return {"photo_links" : [url for _,url in photos]}




def generate_audio_node(state: GraphState) -> dict:
    print("---NODE: Generating Audio---")
    text_to_read = state.story.text
    audio_link = generate_audio(text_to_read=text_to_read,
                    test=state.test 
                   )
    return {"audio_link": audio_link}




if __name__ == "__main__":

    """
        Workflow generates data on the api provider side and returns a final
        state with created media
    """
    workflow = StateGraph(GraphState)

    workflow.add_node("generate_story", generate_story_node)
    workflow.add_node("generate_image_prompts", generate_image_prompts_node)
    workflow.add_node("generate_images", generate_images_node)
    workflow.add_node("generate_audio", generate_audio_node)

    workflow.set_entry_point("generate_story")

    workflow.add_edge("generate_story", "generate_image_prompts")
    workflow.add_edge("generate_image_prompts", "generate_images")
    workflow.add_edge("generate_images", "generate_audio")
    workflow.add_edge("generate_audio", END)


    # TODO:
    # - this mechanism of storing in the memory could be used to run the graph after exception from some specific node
    # - or to introduce human in the loop
    # - at some point we have to implement rerun mechanism for the whole workflow, that omits filled in nodes
    #   such that we don't need to replicate the whole generation again
    checkpointer = InMemorySaver()

    app = workflow.compile(checkpointer=checkpointer)
    # app.get_graph().print_ascii()

    config = {
        "configurable": {
            "thread_id": uuid.uuid4(),
        }
    }

    TITLE = "Short story about quick fox"
    STORY_SLUG = TITLE.lower().replace(" ", "_")

    workflow_initial_state = {
        "topic": "Short story about quick fox",
        "story_slug": STORY_SLUG,
        "test": False,
        "story": None,
        "image_prompts": None,
        "photo_links": None,
        "audio_link": None
    }

    config = {
        "configurable": {
            "thread_id": uuid.uuid4(),
        }
    }

    
    initial_state = GraphState(**workflow_initial_state)
    try:
        final_state = app.invoke(initial_state,config)
    except Exception as e:
        final_state = app.get_state(config).values
        print(final_state)
        print(f"Exception happened: {e}")

    final_state_pydantic = GraphState(**final_state)

    ROOT_DATA = Path(__file__).resolve().parent / "data" / "final_states" 
    STATE_OUTPUT_FOLDER = ROOT_DATA / STORY_SLUG
    STATE_OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    file_name = Path(initial_state.topic.replace(" ", "_").lower())

    final_state_path= STATE_OUTPUT_FOLDER / file_name.with_suffix(".json")

    print("\n---PIPELINE COMPLETE---")
    
    with open(final_state_path, "w", encoding="utf-8") as file:
        file.write(final_state_pydantic.model_dump_json(indent=2))
    print(f"changes saved in {final_state_path}")


