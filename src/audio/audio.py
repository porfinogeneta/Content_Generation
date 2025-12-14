from dotenv import load_dotenv
from elevenlabs import ElevenLabs, VoiceSettings
from elevenlabs.play import play
import tempfile
import os
import time
from pathlib import Path
from pydub import AudioSegment
import soundfile as sf
import pyrubberband as pyrb
from consts.test_consts import AUDIO_FILE
import fal_client
import requests


load_dotenv()


class FalClient:
    def __init__(self):
        pass

    def __submit(self, text_to_read: str) -> str:
        """
            Returnes url with data
        """
        handler = fal_client.submit(
            "fal-ai/orpheus-tts",
            arguments={
                "text": text_to_read
            },
            webhook_url="https://optional.webhook.url/for/results",
        )

        request_id = handler.request_id
        return fal_client.result("fal-ai/orpheus-tts", request_id)

    def text_to_speech_convert(self, text_to_read: str) -> str:
        """
            Generator function returning stream for audio processing.
        """
        url = self.__submit(text_to_read).get("audio", None).get("url", None)

        if not url:
            raise Exception("No audio generated")
        return url



def generate_audio(text_to_read: str,
                    test=False) -> Path:
    
    """
        Generates audio in audio provider, returns link to the resource.
    """
    if test:
        return AUDIO_FILE
    

    # FALAI CLIENT
    fal_client = FalClient()
    return fal_client.text_to_speech_convert(text_to_read)


    


if __name__ == "__main__":
    print(generate_audio(text_to_read="Before I adopted Buster, my evenings were quiet. I'd come home from work, make dinner, watch some TV, and maybe read a book. My apartment was always spotless, and my schedule was entirely my own. Then came Buster, a scruffy terrier mix with the biggest, most soulful eyes I'd ever seen. He was a rescue, a bit timid at first, but full of an energy I hadn't anticipated.",
                ))
# speed_up_audio(Path("audio_original_1762291021.9402099.mp3"), speed_factor=2.0)



# /Users/szymon/Documents/projekciki/Content_Generation/src/data/audio/audio_original_1762291021.9402099.mp3
