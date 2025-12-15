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
DATA_PATH = ROOT_SRC / "data"


# class EditorConfig:
#     """
#         Holds editor config values
#     """
#     DATA_PATH = 
    

# editing videos using MoviePy
class Editor:

    def __init__(self, 
                title: str,
                story_slug: str,
                scenes: List[str],
                audio_url: str,
                playback_speed: float,
                image_urls: List[str],
                ):
        
        self.title = title
        self.story_slug = story_slug
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


        audio_clip = AudioFileClip(audio_file)

        audio_duration = audio_clip.duration

        # time per image is a function of image text length
        # those are the chunks of original text, used for images generation
        images_texts_length = [len(elem["text"]) for elem in self.scenes]
        total_length = sum(images_texts_length)
        # get ratio of sentence length to total_length
        ratios = [e / total_length for e in images_texts_length]
        time_per_images = [audio_duration * ratio for ratio in ratios]
        print(time_per_images)

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
        

        timestamp_with_subtitles = self.generate_subtitles(audio_path=audio_file, subtitles_chunk_size=2)
        srt_file = self.create_srt_file(timestamp_with_subtitles)

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
                                        size=(video.w - 100, text_box_height), 
                                        )

        subtitles_clip = SubtitlesClip(
            srt_file,
            make_textclip=generator, 
            encoding='utf-8'
        )

        # Ensure subtitles last as long as the video
        subtitles_clip = subtitles_clip.with_duration(video.duration)

        # Position: 'center' horizontally, and bottom 20% vertically
        # We subtract the text_box_height to ensure it doesn't bleed off the bottom
        position_y = self.video_size[1] - text_box_height - 50 
        subtitles_clip = subtitles_clip.with_position(('center', position_y))

        video = CompositeVideoClip([video, subtitles_clip])

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
    STORY_SLUG = movie_data.get("story_slug", None)

    editor = Editor(title=TITLE,
                    story_slug=STORY_SLUG,
                    playback_speed=3.0,
                    scenes=movie_data["image_prompts"],
                    audio_url=movie_data["audio_link"],
                    image_urls=movie_data["photo_links"])
    
    editor.create_video()
