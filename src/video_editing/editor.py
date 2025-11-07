from moviepy import ImageClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip
import requests
from typing import List
from pathlib import Path
import json
import concurrent.futures
import numpy as np
from animations import slide_in_effect


ROOT_SRC = Path(__file__).resolve().parent.parent
INPUT_DATA_PATH = ROOT_SRC / "data" / "final_states"
BASE_OUTPUT_PATH = ROOT_SRC / "data" / "videos"

# editing videos using MoviePy
class Editor:
    def __init__(self, title: str, scenes: List[str], audio: str, images: List[str]):
        self.title = title
        self.scenes = scenes
        self.audio = audio
        self.images = images
        self.video_size = (1080, 1920)
        self.zoom_factor = 0.30
    
    # fetches remotely stored data, returns path to local file
    def fetch_data(self, url: str, index: int) -> List[Path]:
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            file_name = Path(f"temp_image_{index}.jpg")
            file_name_path = ROOT_SRC / Path("data") / Path("images") / file_name
            with open(file_name_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return file_name_path
        except requests.exceptions.RequestException as e:
            print(f"Error downloading image {url}: {e}")
            raise Exception("unable to download")

    

    def create_video(self):

        # concurrently fetch images
        MAX_WORKERS = 5
        image_files = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # mapping future objects to index
            future_to_index = {
                # resubmission probably should be on the generate_image side
                executor.submit(self.fetch_data, url=url, index=i): i 
                for i, url in enumerate(self.images)
            }

        for future in concurrent.futures.as_completed(future_to_index):
            i = future_to_index[future]
            
            try:
                # wait for the thread to complete, return a value
                url = future.result()
                image_files.append((i, url))
            except Exception as exc:
                print(f"Image fetch failed: {exc}.")

        image_files.sort(key=lambda elem: elem[0])

        # will be replaced with fetch_data, for now we store audio locally
        audio = self.audio
        audio_clip = AudioFileClip(audio)

        audio_duration = audio_clip.duration

        # time per image is a function of image text length
        # those are the chunks of original text, used for images generation
        images_texts_length = [len(elem["text"]) for elem in self.scenes]
        total_length = sum(images_texts_length)
        # get ratio of sentence length to total_length
        ratios = [e / total_length for e in images_texts_length]
        time_per_images = [audio_duration * ratio for ratio in ratios]

        
        
        clips = []
        for (idx,img),time_per_image in zip(image_files,time_per_images):
            clip = ImageClip(img).with_duration(time_per_image)
            
            

            # Apply all transformations sequentially
            animated_clip = slide_in_effect(clip, time_per_image / 3, self.video_size[0])
            if idx > 0:
                animiated_clip_transition = animated_clip.crossfadein(time_per_image / 3).with_start(time_per_images[i])
            # animated_clip = animated_clip.rotated(get_rotation, resample='bicubic')
            # animated_clip = animated_clip.resized(lambda t: 1 + (self.zoom_factor) * t / zoom_duration)
            
            final_clip = CompositeVideoClip([animated_clip], size=self.video_size).with_duration(time_per_image)


            # final_clip = CompositeVideoClip([animated_clip.set_position("center")], size=self.video_size).set_duration(time_per_image)
            clips.append(final_clip)


        video = concatenate_videoclips(clips)
        video = video.with_audio(audio_clip)

        # save video
        video.write_videofile(BASE_OUTPUT_PATH / Path(f"{self.title}.mp4"), fps=24)



if __name__ == "__main__":

#     movie_data = {
#     "topic": "Interesting story about move in inspection",
#     "post": {
#         "title": "My Landlord and I Discovered a Secret Room During My Move-In Inspection",
#         "text": "So, I just moved into this charming, albeit slightly creaky, old apartment building downtown. It's got character, you know? High ceilings, original hardwood, and a landlord, Mr. Henderson, who's been managing properties in this city for what feels like a century. He's a stickler for details, which I appreciate, but it also meant our move-in inspection was going to be *thorough*. And I mean *thorough*.\n\nWe started in the living room, documenting every tiny scuff, every paint chip, every slightly loose floorboard. He had a clipboard, a flashlight, and a magnifying glass, no joke. We moved into the master bedroom, which had this rather large, built-in bookshelf in the closet. It looked old, probably original to the building, and a bit rickety, but functional.\n\nMr. Henderson was meticulously checking the back wall of the closet, behind the bookshelf. He was tapping, listening, making notes about the plaster. Suddenly, he stopped. He tapped again, a bit harder, on a specific spot. It sounded distinctly hollow. He frowned, then pushed gently. Nothing. He pushed a bit harder, and to both our astonishment, a faint, almost invisible seam appeared in the wall, running vertically and horizontally.\n\nHis eyes widened. \"Well, I'll be,\" he muttered, completely taken aback. He tried to pry it open, but it was stuck. I offered to help, and together, we managed to get a grip on the edge. With a collective grunt, a section of the wall, about three feet wide and five feet tall, swung inward with a soft creak, revealing a small, dark, dusty, empty room. It was barely big enough for one person to stand in, maybe 4x4 feet, and completely bare except for a thick layer of dust and cobwebs.\n\nWe both just stood there, staring into the void. Mr. Henderson, who had owned and managed this building for over twenty years, was absolutely speechless. \"I... I had no idea,\" he finally stammered, his flashlight beam dancing around the tiny space. \"Never in all my years. This is... incredible!\" We found nothing but a single, very old, empty wooden box in the corner, but the sheer surprise of it was enough. He was so excited, he almost forgot to finish the rest of the inspection. He even joked that it was a 'bonus feature' of the apartment. I'm still trying to figure out what it was used for, but it definitely made for the most interesting move-in inspection of my life.",
#         "tldr": "During my move-in inspection, my meticulous landlord and I accidentally discovered a secret, hidden room behind a built-in bookshelf in my closet, a space he never knew existed despite owning the building for over two decades."
#     },
#     "images_prompts": [
#         {
#             "text": "So, I just moved into this charming, albeit slightly creaky, old apartment building downtown. It's got character, you know? High ceilings, original hardwood, and a landlord, Mr. Henderson, who's been managing properties in this city for what feels like a century.",
#             "img_prompt": "A charming, slightly creaky old apartment building downtown, with high ceilings and original hardwood floors. A wise, older landlord, Mr. Henderson, stands in the foreground, holding a clipboard."
#         },
#         {
#             "text": "He's a stickler for details, which I appreciate, but it also meant our move-in inspection was going to be *thorough*. And I mean *thorough*. We started in the living room, documenting every tiny scuff, every paint chip, every slightly loose floorboard. He had a clipboard, a flashlight, and a magnifying glass, no joke.",
#             "img_prompt": "An older, meticulous landlord, Mr. Henderson, with a clipboard, flashlight, and magnifying glass, inspecting a living room floor, pointing at a tiny scuff. The room is old with character."
#         },
#         {
#             "text": "We moved into the master bedroom, which had this rather large, built-in bookshelf in the closet. It looked old, probably original to the building, and a bit rickety, but functional. Mr. Henderson was meticulously checking the back wall of the closet, behind the bookshelf.",
#             "img_prompt": "Inside an old master bedroom closet, a large, rickety, built-in wooden bookshelf stands against a wall. Mr. Henderson, the landlord, is carefully inspecting the wall behind the bookshelf with a flashlight."
#         },
#         {
#             "text": "He was tapping, listening, making notes about the plaster. Suddenly, he stopped. He tapped again, a bit harder, on a specific spot. It sounded distinctly hollow. He frowned, then pushed gently. Nothing. He pushed a bit harder, and to both our astonishment, a faint, almost invisible seam appeared in the wall, running vertically and horizontally.",
#             "img_prompt": "Close-up of Mr. Henderson's hand tapping a wall behind a bookshelf in a closet. His face shows a look of surprise and curiosity as a faint, almost invisible seam appears in the plaster wall."
#         },
#         {
#             "text": "His eyes widened. \"Well, I'll be,\" he muttered, completely taken aback. He tried to pry it open, but it was stuck. I offered to help, and together, we managed to get a grip on the edge. With a collective grunt, a section of the wall, about three feet wide and five feet tall, swung inward with a soft creak, revealing a small, dark, dusty, empty room.",
#             "img_prompt": "The landlord, Mr. Henderson, and the tenant, working together, prying open a section of a wall in a closet. The wall swings inward with a creak, revealing a small, dark, dusty, empty secret room."
#         },
#         {
#             "text": "It was barely big enough for one person to stand in, maybe 4x4 feet, and completely bare except for a thick layer of dust and cobwebs.",
#             "img_prompt": "A small, dark, dusty, empty secret room, approximately 4x4 feet, revealed behind a hidden door in a closet. Cobwebs hang from the ceiling and a thick layer of dust covers the floor."
#         },
#         {
#             "text": "We both just stood there, staring into the void. Mr. Henderson, who had owned and managed this building for over twenty years, was absolutely speechless. \"I... I had no idea,\" he finally stammered, his flashlight beam dancing around the tiny space. \"Never in all my years. This is... incredible!\" We found nothing but a single, very old, empty wooden box in the corner, but the sheer surprise of it was enough.",
#             "img_prompt": "The landlord, Mr. Henderson, and the tenant standing in awe, looking into the newly discovered secret room. Mr. Henderson's face shows utter surprise, and his flashlight beam illuminates a single, very old, empty wooden box in a dusty corner of the small room."
#         },
#         {
#             "text": "He was so excited, he almost forgot to finish the rest of the inspection. He even joked that it was a 'bonus feature' of the apartment. I'm still trying to figure out what it was used for, but it definitely made for the most interesting move-in inspection of my life.",
#             "img_prompt": "Mr. Henderson, the landlord, smiling excitedly, gesturing towards the secret room, as if presenting a 'bonus feature'. The tenant looks on, amused and curious. The scene conveys a sense of wonder and discovery."
#         }
#     ],
#     "photos_links": [
#         "https://v3b.fal.media/files/b/penguin/xah1RcdUnV3nejwE0QpZl.jpg",
#         "https://v3b.fal.media/files/b/kangaroo/4Q6mTU24xJx-SrGXvVXHR.jpg",
#         "https://v3b.fal.media/files/b/rabbit/NtXDnZkBy-w7dS3YSDKOc.jpg",
#         "https://v3b.fal.media/files/b/rabbit/tLm2yXma0YbVzf7Jsty5o.jpg",
#         "https://v3b.fal.media/files/b/tiger/HwKA9_1TphYftm0LdCzsQ.jpg",
#         "https://v3b.fal.media/files/b/kangaroo/E6uTruTN3hi6a4ij1SVfo.jpg",
#         "https://v3b.fal.media/files/b/monkey/bJ2dyJ-5YsU7JOsqEZHJk.jpg",
#         "https://v3b.fal.media/files/b/rabbit/Psdod48OPrugXP_5P6rgv.jpg"
#     ],
#     "audio_link": "/Users/szymon/Documents/projekciki/Content_Generation/src/data/audio/interesting_story_about_move_in_inspection/_2.0_audio_original_1762513265.316447.wav"
# }

    title_ = "short_story_about_quick_fox.json"
    INPUT_DICT_PATH = INPUT_DATA_PATH / title_
    movie_data = None

    try:
        with open(INPUT_DICT_PATH, 'r') as json_file:
            movie_data = json.load(json_file)
    except:
        raise Exception("file")

    editor = Editor(title="hello",
                    scenes=movie_data["image_prompts"],
                    audio=movie_data["audio_link"],
                    images=movie_data["photo_links"])
    
    editor.create_video()
