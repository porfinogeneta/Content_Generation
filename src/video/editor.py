from moviepy import ImageClip, TextClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip
import requests
from typing import List
from pathlib import Path
import json
import tempfile
import concurrent.futures
import numpy as np
from moviepy.video.fx.CrossFadeIn import CrossFadeIn
from faster_whisper import WhisperModel
from moviepy.video.tools.subtitles import SubtitlesClip
from PIL import ImageFont
from typing import List, Tuple
import math
import soundfile as sf
import pyrubberband as pyrb
import pysrt
import os
import time

ROOT_SRC = Path(__file__).resolve().parent.parent
INPUT_DATA_PATH = ROOT_SRC / "data" / "final_states"
DATA_PATH = ROOT_SRC / "data"


    

# editing videos using MoviePy
class Editor:

    def __init__(self, 
                title: str,
                scenes: List[str],
                audio_url: str,
                playback_speed: float,
                image_urls: List[str],
                ):
        
        self.title = title
        self.story_slug = title.lower().replace(" ", "_")
        self.scenes = scenes
        self.audio_url = audio_url
        self.playback_speed = playback_speed
        self.image_urls = image_urls
        self.video_size = (1080, 1920)
        self.zoom_factor = 0.30
        
        # output directories
        self.audio_dir = DATA_PATH / self.story_slug / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        self.imgs_dir = DATA_PATH / self.story_slug / "images"
        self.imgs_dir.mkdir(parents=True, exist_ok=True)

        self.videos_dir = DATA_PATH / self.story_slug / "video"
        self.videos_dir.mkdir(parents=True, exist_ok=True)

        self.srt_path = DATA_PATH / self.story_slug / Path(f"{self.story_slug}_subtitles")
        self.srt_path.mkdir(parents=True, exist_ok=True)

        # has to be predefined earlier
        self.font_path =  DATA_PATH / "fonts" / Path("TikTokSans_28pt-Medium.ttf")
        # self.font_path = "/Users/szymon/Documents/projekciki/Content_Generation/src/data/fonts/TikTokSans_28pt-Medium.ttf"
        
    
    # fetches remotely stored data, returns path to local file
    def fetch_data(self, url: str, destination: Path, suffix: str, index: int) -> Path:

        if url.startswith("https:/") and not url.startswith("https://"):
            url = url.replace("https:/", "https://", 1)

        try:

            # exisitng path
            if destination.is_dir():
                file_name = Path(f"_{index}{suffix}")
                final_path = destination / file_name
            else:
                # temporary file
                final_path = destination


            response = requests.get(url, stream=True)
            response.raise_for_status()
        
            
            with open(final_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return final_path
        
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {url}: {e}")
            raise Exception(e)

    def transcribe(self, audio_path: Path):
        model = WhisperModel("small")
        segments, info = model.transcribe(audio_path, word_timestamps=True)
        return info.language, segments
    
    def generate_subtitles(self, audio_path: Path, subtitles_chunk_size: int):
        """
            Returns a list of tuples containing list of words, alongside timestamps:
            [(start1, end1, word1), (start2, end2, word2)]
        """
        complete_timestamp_and_words: List[Tuple[float, float, str]] = []
        lang, segments = self.transcribe(audio_path)
        for segment in segments:
            segment_timestamp_words: List[Tuple[float, float, str]] = []
            # each segment contains Word(start=np.float64(7.76), end=np.float64(7.88), word=' Today', probability=np.float64(0.9799808859825134))
            # a list of Word objects
            for word in segment.words:
                # we've got enough subtitles in this part
                segment_timestamp_words.append((word.start, word.end, word.word))

                if len(segment_timestamp_words) >= subtitles_chunk_size:
                    # print(segment_timestamp_words)
                    # concat current segment
                    # extract words, start and end is the start of the first word and end of the last word
                    start = segment_timestamp_words[0][0]
                    end = segment_timestamp_words[-1][1]
                    words = "".join([t[2] for t in segment_timestamp_words])
                    complete_timestamp_and_words += [(start, end, words)]
                    segment_timestamp_words = []
            
            # concat remaining words in a segment
            if len(segment_timestamp_words) != 0:
                start = segment_timestamp_words[0][0]
                end = segment_timestamp_words[-1][1]
                # create a subtitle from the string
                words = "".join([t[2] for t in segment_timestamp_words])
                complete_timestamp_and_words += [(start, end, words)]
                segment_timestamp_words = []
                
        return complete_timestamp_and_words
    
    def format_time(self, seconds):

        hours = math.floor(seconds / 3600)
        seconds %= 3600
        minutes = math.floor(seconds / 60)
        seconds %= 60
        milliseconds = round((seconds - math.floor(seconds)) * 1000)
        seconds = math.floor(seconds)
        formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
        return formatted_time
    
    def create_srt_file(self, segment_timestamp_words: List[Tuple[float, float, str]]):

        final_output_file = self.srt_path / Path("subtitles.srt")

        with open(final_output_file, "w") as file:
            text = ""
            for index, (start, end, subtitle) in enumerate(segment_timestamp_words):
                text += f"{str(index+1)} \n"
                text += f"{self.format_time(start)} --> {self.format_time(end)}\n"
                text += f"{subtitle} \n"
                text += "\n"
            text = text.strip()
            file.write(text)

        return final_output_file

    

    def fetch_audio(self) -> Path:
        """
            Fetches audio file and speeds it up
        """

        

        final_output_path = self.audio_dir / "final_audio.wav"

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_path = Path(tmp.name)

        # allow fetch data to open
        tmp.close()
        try:

            self.fetch_data(url=self.audio_url, destination=temp_path, suffix=".wav", index=0)

            # # put file pointer at the beginning
            # tmp.seek(0)

            # speed up and return wav
            y, sr = sf.read(temp_path)
            
            # Play back at 1.5X speed
            y_stretch = pyrb.time_stretch(y, sr, self.playback_speed)
            # Play back two 1.5x tones
            # y_shift = pyrb.pitch_shift(y, sr, 1.5)

            sf.write(final_output_path, y_stretch, sr, format='wav')

            return final_output_path
        
        finally:
            # because we didn't delete temp file (delete=False)
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def fetch_images(self) -> List[str]:
        """
        Docstring for fetch_images
        
        :param self: Description

        Fetches images and stores data in images folder:

        data/"story_slug"/images
        """
        # concurrently fetch images
        MAX_WORKERS = 5
        
        image_files = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # mapping future objects to index
            future_to_index = {
                # resubmission probably should be on the generate_image side
                executor.submit(self.fetch_data, url=url, destination=self.imgs_dir, suffix=".jpg", index=i): i 
                for i, url in enumerate(self.image_urls)
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

        return image_files
    
    def __convert_time_seconds(self, t: time):
        return (t.hour * 60 + t.minute) * 60 + t.second + (t.microsecond / 1000000.0)
    
    # def determine_time(self, transcript: Path, audio_duration: float):
    #     """
    #         Gets amount of words in each image, then calculates
    #         the percentage of words each scene should take

    #         Returns time per images, based on the transcript file with the ration
    #         taken based on percentages in each scene
    #     """
    #     length_in_words = [len(elem["text"].split()) for elem in self.scenes]
    #     total_word_len = sum(length_in_words)
    #     ratios = [l/total_word_len for l in length_in_words]

    #     # read srt file into tuples:
    #     # start in seconds, end in seconds, words in each chunk of transcript
    #     # (start, end, words)
    #     transcript_tuples = []
    #     all_words_cnt = 0
    #     subs = pysrt.open(transcript)
    #     # subs = pysrt.open(transcript)
    #     for sub in subs:
    #         # divide to convert into float
    #         start_time: time = self.__convert_time_seconds(sub.start.to_time())
    #         end_time: time =  self.__convert_time_seconds(sub.end.to_time())
    #         words_amount = len(sub.text.strip().split())
    #         transcript_tuples.append([start_time, end_time, words_amount])
    #         all_words_cnt += words_amount
           
    #     # ratio of all the words in the transcript
    #     transcript_tuples = [[s, e, l / all_words_cnt] for s,e,l in transcript_tuples]

    #     # construct time per images array, containing time needed to fill in the ratio for a given image
    #     time_per_images = []
    #     i = 0
    #     j = 0
    #     while i < len(self.scenes):
    #         # gather ratios until getting a ratio bigger or equal to ratio for a specific image
    #         start, _, _ = transcript_tuples[j]
    #         gathered_ratio = 0
    #         while j < len(transcript_tuples):
    #             _, _, r = transcript_tuples[j]
    #             gathered_ratio += r
    #             j += 1
    #             if gathered_ratio > ratios[i]:
    #                 break

                
    #         # last tuple should be considered as the end value
    #         _, end, _ = transcript_tuples[j - 1]
    #         time_per_images.append(end - start)
    #         i += 1

    #     # make images match the total duration exaclty
    #     calculated_total = sum(time_per_images)
    #     if calculated_total > 0:
    #         correction_factor = audio_duration / calculated_total
    #         time_per_images = [t * correction_factor for t in time_per_images]

        
    #     return time_per_images

    def determine_time(self, transcript: Path, audio_duration: float):
        
        # 1. Calculate how many words are in each SCENE prompt
        scene_word_counts = [len(elem["text"].split()) for elem in self.scenes]
        total_prompt_words = sum(scene_word_counts)
        
        # 2. Parse the SRT to map "Word Count" -> "Time it finishes"
        # We create a list of (cumulative_words, end_time)
        subs = pysrt.open(transcript)
        srt_map = []
        cumulative_words = 0
        
        for sub in subs:
            # simple word count for this subtitle
            words_in_sub = len(sub.text.strip().split())
            cumulative_words += words_in_sub
            
            end_time = self.__convert_time_seconds(sub.end.to_time())
            srt_map.append((cumulative_words, end_time))

        # 3. Determine duration for each image
        time_per_images = []
        last_switch_time = 0.0
        current_scene_word_target = 0

        # Iterate through scenes
        for i in range(len(self.scenes)):
            # How many words does this scene (and previous ones) represent?
            current_scene_word_target += scene_word_counts[i]
            
            # What is the Ratio of this target relative to total prompt words?
            # e.g., Scene 1 is 10 words out of 100 total = 10%
            ratio = current_scene_word_target / total_prompt_words
            
            # How many spoken words in the SRT does this correspond to?
            # If SRT has 500 words total, we look for word #50.
            target_spoken_word_count = ratio * cumulative_words
            
            # FIND THE TIMESTAMP:
            # Find the subtitle that contains this target word count
            # We look for the first subtitle where cumulative words >= target
            found_time = audio_duration # Default to end
            
            for (words_done, time_done) in srt_map:
                if words_done >= target_spoken_word_count:
                    found_time = time_done
                    break
            
            # Duration is: The time we found MINUS the time the previous scene ended
            duration = found_time - last_switch_time
            
            # Sanity check for very short durations
            if duration < 0.5: duration = 0.5
            
            time_per_images.append(duration)
            last_switch_time = found_time

        # 4. Final Adjustment
        # Ensure the sum of durations matches audio_duration exactly 
        # (Usually just adjusting the last frame slightly)
        total_calculated = sum(time_per_images)
        diff = audio_duration - total_calculated
        # Add the difference to the last slide
        if time_per_images:
            time_per_images[-1] += diff

        return time_per_images

    

    def resize_and_crop_image(self, image_path: str, target_size: Tuple[int, int]) -> str:
        """
        Pre-processes image to fit target size (cover mode) to save RAM during rendering.
        Returns path to processed image.
        """
        with ImageClip(image_path) as img:
            # Resize so that the smallest dimension matches the target
            w, h = img.size
            target_w, target_h = target_size
            
            # Calculate aspect ratios
            aspect_ratio = w / h
            target_aspect = target_w / target_h
            
            if aspect_ratio > target_aspect:
                # Image is wider than target
                new_h = target_h
                new_w = int(target_h * aspect_ratio)
            else:
                # Image is taller/same as target
                new_w = target_w
                new_h = int(target_w / aspect_ratio)
                
            # Resize once statically
            img_resized = img.resized(new_size=(new_w, new_h))
            
            # Center crop
            img_cropped = img_resized.cropped(
                x1=(new_w/2) - (target_w/2),
                y1=(new_h/2) - (target_h/2),
                width=target_w,
                height=target_h
            )
            
            # Save temp file to avoid re-processing every frame
            temp_processed = Path(image_path).parent / f"processed_{Path(image_path).name}.png"
            img_cropped.save_frame(str(temp_processed), t=0)
            return str(temp_processed)
            

    def create_video(self):

        
        # TODO: maybe rewriting it to async would be better, but too much work lol, 
        # it would be cheaper in terms of computing (one thread instead of many)
        # concurrently fetch data
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_images = executor.submit(self.fetch_images)
            future_audio = executor.submit(self.fetch_audio)

            # wait for resources, returns path to resources
            image_files = future_images.result()
            audio_file = future_audio.result()


        audio_clip = AudioFileClip(str(audio_file))
        audio_duration = audio_clip.duration

        # subtitles generated
        timestamp_with_subtitles = self.generate_subtitles(audio_path=audio_file, subtitles_chunk_size=2)
        srt_file = self.create_srt_file(timestamp_with_subtitles)

        # determine time for images
        clean_durations = self.determine_time(transcript=srt_file, audio_duration=audio_clip.duration)



        # ADD TRANSITIONS AND ANIMATIONS
        CROSSFADE_DURATION = 1.0
        final_clips_with_transitions = []
        current_start_time = 0.0
        for (idx, img_path), clean_duration in zip(image_files, clean_durations):
            
            # fit image exaclty in the frame

           
            # the clips except for the last one will be extended by an animation
            is_last = (idx == len(image_files) - 1)
            actual_duration = clean_duration if is_last else clean_duration + CROSSFADE_DURATION

            clip = ImageClip(img_path).with_duration(actual_duration)

            # Zoom animation with proper closure
            animated_clip = clip.resized(lambda t, dur=clean_duration: 1 + (self.zoom_factor) * t / dur)
            centered_clip = animated_clip.with_position("center")
            animated_clip = CompositeVideoClip([centered_clip], size=self.video_size)
            
            # Apply crossfade for clips after the first
            if idx > 0:
                animated_clip = CrossFadeIn(CROSSFADE_DURATION).apply(animated_clip)
            
            final_clip = animated_clip.with_start(current_start_time)

            final_clips_with_transitions.append(final_clip)
            current_start_time += clean_duration


        # since all clips were added with proper start times we can simply put everything into
        # clips generation
        video_track = CompositeVideoClip(final_clips_with_transitions)
        video_track.with_duration(audio_duration)

        # This prevents the text from being centered in a full-screen box
        text_box_height = 400 

        generator = lambda text: TextClip(
                                        font=self.font_path,
                                        text=text,
                                        color='white',
                                        text_align='center',
                                        font_size=100,
                                        stroke_color='black',
                                        # stroke_width=4,
                                        method='caption',
                                        size=(video_track.w - 100, text_box_height), 
                                        )

        subtitles_clip = SubtitlesClip(
            srt_file,
            make_textclip=generator, 
            encoding='utf-8'
        )

        # Ensure subtitles last as long as the video
        subtitles_clip = subtitles_clip.with_duration(video_track.duration)

        # Position: 'center' horizontally, and bottom 20% vertically
        # We subtract the text_box_height to ensure it doesn't bleed off the bottom
        position_y = self.video_size[1] - text_box_height - 50 
        subtitles_clip = subtitles_clip.with_position(('center', position_y))

        video = CompositeVideoClip([video_track, subtitles_clip])

        # ADD AUDIO
        video = video.with_audio(audio_clip)

        # save video
        final_output_path = self.videos_dir / Path(f"{self.story_slug}.mp4")
        video.write_videofile(final_output_path, fps=24)



if __name__ == "__main__":

    title_ = "short_story_about_quick_fox"
    INPUT_DICT_PATH = INPUT_DATA_PATH / title_ / Path(f"{title_}.json")
    movie_data = None

    try:
        with open(INPUT_DICT_PATH, 'r') as json_file:
            movie_data = json.load(json_file)
    except:
        raise Exception("file")
    
    TITLE = movie_data.get("title", None)

    editor = Editor(title=TITLE,
                    playback_speed=1.5,
                    scenes=movie_data["image_prompts"],
                    audio_url=movie_data["audio_link"],
                    image_urls=movie_data["photo_links"])
    
    editor.create_video()
