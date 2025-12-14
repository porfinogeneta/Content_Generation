from moviepy import ImageClip, TextClip, concatenate_videoclips, AudioFileClip, CompositeVideoClip
import requests
from typing import List
from pathlib import Path
import json
import tempfile
import concurrent.futures
import numpy as np
from animations import slide_in_effect
from moviepy.video.fx.CrossFadeIn import CrossFadeIn
from faster_whisper import WhisperModel
from moviepy.video.tools.subtitles import SubtitlesClip
from PIL import ImageFont
from typing import List, Tuple
import math
import soundfile as sf
import pyrubberband as pyrb
import os

ROOT_SRC = Path(__file__).resolve().parent.parent
INPUT_DATA_PATH = ROOT_SRC / "data" / "final_states"
BASE_OUTPUT_PATH = ROOT_SRC / "data" / "videos"
FONT_PATH = ROOT_SRC / "data" / "subtitles" / "fonts"
OUTPUT_SRT_PATH = ROOT_SRC / "data" / "subtitles" / "srt"

# editing videos using MoviePy
class Editor:
    def __init__(self, 
                title: str,
                story_slug: str,
                scenes: List[str],
                audio: str,
                playback_speed: float,
                images: List[str],
                font_path:str = FONT_PATH / Path("TikTokSans_28pt-Medium.ttf"),
                srt_path: str = OUTPUT_SRT_PATH / Path("test.srt")):
        
        self.title = title
        self.story_slug = story_slug
        self.scenes = scenes
        self.audio = audio
        self.playback_speed = 2.0
        self.images = images
        self.video_size = (1080, 1920)
        self.zoom_factor = 0.30
        self.font_path = font_path
        self.srt_path = srt_path
    
    # fetches remotely stored data, returns path to local file
    def fetch_data(self, url: str, destination: Path, suffix: str, index: int) -> Path:
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
            print(f"Error downloading image {url}: {e}")
            raise Exception("unable to download")

    def transcribe(self):
        model = WhisperModel("small")
        segments, info = model.transcribe(self.audio, word_timestamps=True)
        return info.language, segments
    
    def generate_subtitles(self, subtitles_chunk_size: int):
        """
            Returns a list of tuples containing list of words, alongside timestamps:
            [(start1, end1, word1), (start2, end2, word2)]
        """
        complete_timestamp_and_words: List[Tuple[float, float, str]] = []
        lang, segments = self.transcribe()
        for segment in segments:
            segment_timestamp_words: List[Tuple[float, float, str]] = []
            # each segment contains Word(start=np.float64(7.76), end=np.float64(7.88), word=' Today', probability=np.float64(0.9799808859825134))
            # a list of Word objects
            for word in segment.words:
                # we've got enough subtitles in this part
                segment_timestamp_words.append((word.start, word.end, word.word))

                if len(segment_timestamp_words) >= subtitles_chunk_size:
                    print(segment_timestamp_words)
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
        with open(self.srt_path, "w") as file:
            text = ""
            for index, (start, end, subtitle) in enumerate(segment_timestamp_words):
                text += f"{str(index+1)} \n"
                text += f"{self.format_time(start)} --> {self.format_time(end)}\n"
                text += f"{subtitle} \n"
                text += "\n"
            text = text.strip()
            file.write(text)

    

    def fetch_audio(self):
        """
            Fetches audio file and speeds it up
        """
        tmp = tempfile.NamedTemporaryFile(suffix="wav", delete=False)
        temp_path = Path(tmp.name)

        # allow fetch data to open
        tmp.close()
        try:

            downloaded_path = self.fetch_data(url=self.audio, destination=temp_path, suffix=".wav", index=0)

            # put file pointer at the beginning
            temp_file.seek(0)

            # speed up and return wav
            y, sr = sf.read(temp_file)
            
            # Play back at 1.5X speed
            y_stretch = pyrb.time_stretch(y, sr, speed_factor)
            # Play back two 1.5x tones
            # y_shift = pyrb.pitch_shift(y, sr, 1.5)

            sf.write(output_path, y_stretch, sr, format='wav')
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
        PATH = ROOT_SRC / Path("data") / Path(self.story_slug) / Path("images")
        image_files = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # mapping future objects to index
            future_to_index = {
                # resubmission probably should be on the generate_image side
                executor.submit(self.fetch_data, url=url, path=PATH, suffix=".jpg", index=i): i 
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

        return image_files
            

    async def create_video(self):

        
        # TODO: maybe rewriting it to async would be better, but too much work lol, 
        # it would be cheaper in terms of computing (one thread instead of many)
        # concurrently fetch data
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_images = executor.submit(self.fetch_images)
            future_audio = executor.submit(self.fetch_audio)

            # wait for resources
            images = future_images.result()
            audio = future_audio.result()



        audio_clip = AudioFileClip(audio)

        audio_duration = audio_clip.duration

        # time per image is a function of image text length
        # those are the chunks of original text, used for images generation
        images_texts_length = [len(elem["text"]) for elem in self.scenes]
        total_length = sum(images_texts_length)
        # get ratio of sentence length to total_length
        ratios = [e / total_length for e in images_texts_length]
        time_per_images = [audio_duration * ratio for ratio in ratios]

        # ADD TRANSITIONS AND ANIMATIONS
        animated_clips = []
        for (idx, img), time_per_image in zip(image_files, time_per_images):
            
            
            if idx != 0:
                clip = ImageClip(img).with_duration(time_per_image + time_per_image/3)
            else:
                clip = ImageClip(img).with_duration(time_per_image)

            # Zoom animation with proper closure
            animated_clip = clip.resized(lambda t, dur=time_per_image: 1 + (self.zoom_factor) * t / dur)
            centered_clip = animated_clip.with_position("center")
            animated_clip = CompositeVideoClip([centered_clip], size=self.video_size)
            
            # Apply crossfade for clips after the first
            if idx > 0 and idx < len(image_files):
                FADE_DURATION = time_per_image / 3
                animated_clip = CrossFadeIn(FADE_DURATION).apply(animated_clip)
            
            animated_clips.append(animated_clip)

        # Create the final video with overlapping crossfades
        if len(animated_clips) > 0:
            final_clips = [animated_clips[0]]
            current_time = animated_clips[0].duration
            
            for i in range(1, len(animated_clips)):
                FADE_DURATION = time_per_images[i] / 3
                # Start this clip earlier so it overlaps with previous clip
                clip_with_fade = animated_clips[i].with_start(current_time - FADE_DURATION)
                final_clips.append(clip_with_fade)
                current_time += (animated_clips[i].duration - FADE_DURATION)
            
            # final_clips.append(animated_clips[len(animated_clips) - 1])
            
            video = CompositeVideoClip(final_clips)
        else:
            raise Exception("movie should contain images")

        # ADD SUBTITLES
        timestamp_with_subtitles = self.generate_subtitles(subtitles_chunk_size=2)
        self.create_srt_file(timestamp_with_subtitles)

        generator = lambda text: TextClip(
                                        font=self.font_path,
                                        text=text, 
                                        color='white',
                                        text_align='center',
                                        font_size=100,
                                        stroke_color='black',
                                        method='caption',
                                        size=(video.w - 100, video.h),
                                        )
        
        subtitles_clip = SubtitlesClip(
            self.srt_path,
            make_textclip=generator, 
            encoding='utf-8'
        ).with_position(('center', self.video_size[1] - self.video_size[1]/3)) 
        
        video = CompositeVideoClip([video, subtitles_clip])

        # ADD AUDIO
        video = video.with_audio(audio_clip)

        # save video
        video.write_videofile(BASE_OUTPUT_PATH / Path(f"{self.title}.mp4"), fps=24)



if __name__ == "__main__":

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
