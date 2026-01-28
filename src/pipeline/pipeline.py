

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from typing import List, Tuple
import concurrent.futures
from pathlib import Path
import uuid
from langgraph.checkpoint.memory import InMemorySaver
import re

from story.story import generate_story
from schemas.schemas import ImagesPromptsOutput, GraphState
from images.prompt_story import generate_images_prompts
from images.images import generate_image
from audio.audio import generate_audio, generate_text_to_read



class Pipeline:
    ROOT_DATA = Path(__file__).resolve().parent.parent / "data" / "final_states" 
    MAX_WORKERS = 5

    def __init__(self, topic: str, test: bool =False):
        """
            Initializes workflow and it's configuration.
        """
        self.topic = topic
        self.story_slug = self.topic.replace(" ", "_").lower()
        self.test = test
        self.workflow = self.__create_workflow()
        self.workflow_initial_state, self.config = self.__configure_workflow()



    def workflow_compile_and_run(self):
        """
        Docstring for workflow_compile_and_run
        
        :param self: Description
        :param workflow: Description
        :param workflow_initial_state: Description
        :param config: Description

        Runs the whole workflow and saves data in a file.
        """
        # TODO:
        # - this mechanism of storing in the memory could be used to run the graph after exception from some specific node
        # - or to introduce human in the loop
        # - at some point we have to implement rerun mechanism for the whole workflow, that omits filled in nodes
        #   such that we don't need to replicate the whole generation again
        checkpointer = InMemorySaver()

        app = self.workflow.compile(checkpointer=checkpointer)

        initial_state = GraphState(**self.workflow_initial_state)
        try:
            final_state = app.invoke(initial_state,self.config)
        except Exception as e:
            final_state = app.get_state(self.config).values
            print(final_state)
            print(f"Exception happened: {e}")

        final_state_pydantic = GraphState(**final_state)
        self.__save_final_state(final_state_pydantic)

    def __save_final_state(self, final_state_pydantic):
        
        STATE_OUTPUT_FOLDER = Pipeline.ROOT_DATA / self.story_slug
        STATE_OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

        filename = Path(self.story_slug)
        final_state_path= STATE_OUTPUT_FOLDER / filename.with_suffix(".json")

        print("\n---PIPELINE COMPLETE---")
        
        with open(final_state_path, "w", encoding="utf-8") as file:
            file.write(final_state_pydantic.model_dump_json(indent=2))
        print(f"changes saved in {final_state_path}")


    def __create_workflow(self):
        """
            Workflow generates data on the api provider side and returns a final
            state with created media
        """
        workflow = StateGraph(GraphState)

        # STORY
        workflow.add_node("generate_story", self.__generate_story_node)
        # IMAGES (first path)
        workflow.add_node("generate_image_prompts", self.__generate_image_prompts_node)
        workflow.add_node("generate_images", self.__generate_images_node)
        # AUDIO (second path)
        workflow.add_node("generate_audio_text", self.__generate_audio_text_node)
        workflow.add_node("generate_audio_sound", self.__generate_audio_sound_node)

        # entry point
        workflow.set_entry_point("generate_story")

        # images branch
        workflow.add_edge("generate_story", "generate_image_prompts")
        workflow.add_edge("generate_image_prompts", "generate_images")
        workflow.add_edge("generate_images", END)

        # audio branch
        workflow.add_edge("generate_story", "generate_audio_text")
        workflow.add_edge("generate_audio_text", "generate_audio_sound")
        workflow.add_edge("generate_audio_sound", END)
        return workflow


    def __configure_workflow(self):

        config = {
            "configurable": {
                "thread_id": uuid.uuid4(),
            }
        }

        workflow_initial_state = {
            "topic": self.topic,
            "story_slug": self.story_slug,
            "test": self.test,
            "story": None,
            "image_prompts": None,
            "prompts_to_read": None,
            "photo_links": None,
            "audio_links": None
        }

        config = {
            "configurable": {
                "thread_id": uuid.uuid4(),
            }
        }

        return workflow_initial_state, config


    def __generate_story_node(self, state: GraphState) -> dict:
        print("---NODE: Generating Story---")
        return {"story": generate_story(topic=state.topic, test=state.test)}

    def __generate_image_prompts_node(self, state: GraphState) -> dict:
        print("---NODE: Generating prompts for images---")
        story = state.story.text
        return {"image_prompts": generate_images_prompts(full_story_text=story, test=state.test)}

    def __generate_images_node(self, state: GraphState) -> dict:
        print("---NODE: Generating Images & Saving in the cloud---")
        images_prompts_output: List[ImagesPromptsOutput] = state.image_prompts

        prompts = [output.img_prompt for output in images_prompts_output]

        photos: List[Tuple[int,str]] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=Pipeline.MAX_WORKERS) as executor:
            
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

        # sort photos to make sense chronologically
        photos.sort(key=lambda item: item[0])
        return {"photo_links" : [url for _,url in photos]}


    def __split_audio_chunks_senteces(self, text: str):
        audio_chunks = [m.group().strip() for m in re.finditer(r'[^.?!]*[,.?!]', text)]

        # if there is too many sentences, we merge them
        while len(audio_chunks) > 40:
            h = []
            for i in range(0, len(audio_chunks) - 1, 2):
                h.append(audio_chunks[i] + " " + audio_chunks[i+1])
            audio_chunks = h
        
        return audio_chunks



    def __generate_audio_text_node(self, state: GraphState) -> dict:
        """Generate texts that will be later read by llm"""
        print("---NODE: Generating Audio Texts---")
        # texts will be generated based on each sentence from the story
        texts = self.__split_audio_chunks_senteces(text=state.story.text)

        prompts = []
        # concurrently create prompts to read
        with concurrent.futures.ThreadPoolExecutor(max_workers=Pipeline.MAX_WORKERS) as executor:

            # map future to idx
            future_to_index = {
                executor.submit(generate_text_to_read, text=prompt, test=state.test): i
                for i, prompt in enumerate(texts)
            }

            for future in concurrent.futures.as_completed(future_to_index):
                i = future_to_index[future]
                try:
                    prompt = future.result()
                    prompts.append((i, prompt))
                except Exception as e:
                    text = texts[i]
                    print(f"Image generation for prompt #{i} failed: {e}. Prompt: '{text}'")

                
        prompts.sort(key=lambda x: x[0])
        return {"prompts_to_read": [prompt.model_dump() for _,prompt in prompts]}
        
    
    def __generate_audio_sound_node(self, state: GraphState) -> dict:
        print("---NODE: Generating Audio Sounds---")
        texts_to_read = [prompt.text for prompt in state.prompts_to_read]

        urls = []
        # concurrently create prompts to read
        with concurrent.futures.ThreadPoolExecutor(max_workers=Pipeline.MAX_WORKERS) as executor:

            # map future to idx
            future_to_index = {
                executor.submit(generate_audio, text_to_read=prompt, test=state.test): i
                for i, prompt in enumerate(texts_to_read)
            }

            for future in concurrent.futures.as_completed(future_to_index):
                i = future_to_index[future]
                try:
                    url = future.result()
                    urls.append((i, url))
                except Exception as e:
                    text = texts_to_read[i]
                    print(f"Image generation for prompt #{i} failed: {e}. Prompt: '{text}'")

                
        urls.sort(key=lambda x: x[0])

        audio_links = [url for _,url in urls]
        return {"audio_links": audio_links}




if __name__ == "__main__":

    pipeline = Pipeline(topic="My first year of studying", test=False)
    pipeline.workflow_compile_and_run()


    
    
    

    


