from dotenv import load_dotenv
from elevenlabs import ElevenLabs, VoiceSettings
from elevenlabs.play import play
import os
import time
from pathlib import Path
from pydub import AudioSegment
import soundfile as sf
import pyrubberband as pyrb
from consts.test_consts import AUDIO_FILE

load_dotenv()

TEXT = """Before I adopted Buster, my evenings were quiet. I'd come home from work, make dinner, watch some TV, and maybe read a book. My apartment was always spotless, and my schedule was entirely my own. Then came Buster, a scruffy terrier mix with the biggest, most soulful eyes I'd ever seen. He was a rescue, a bit timid at first, but full of an energy I hadn't anticipated. Now, my evenings are a whirlwind. The moment I walk through the door, I'm greeted by a frantic tail wag and a happy bark. Dinner is often delayed because Buster needs his walk, his playtime, and his endless belly rubs. My apartment? Let's just say 'lived-in' is a generous description, with dog toys scattered like confetti and a fine layer of fur on everything. My schedule revolves around his potty breaks, his feeding times, and ensuring he gets enough exercise. I've learned to appreciate early morning walks, even in the rain, and I've discovered a whole community of dog owners at the local park. There are days I'm exhausted, covered in mud, or frustrated by a chewed-up shoe. But then he'll rest his head on my lap, let out a contented sigh, and look up at me with those big, loving eyes, and I remember why I wouldn't trade this chaotic, fur-filled life for anything. He's not just a pet; he's family, a constant source of joy, laughter, and unconditional love. My life is undeniably messier, but it's also infinitely richer."""

ROOT_SRC = Path(__file__).resolve().parent.parent
# print(ROOT)
BASE_OUTPUT_PATH = ROOT_SRC / "data" / "audio"

def generate_audio(text_to_read: str,
                    speed_factor: float = 1.25,
                    prefix: str = "audio_original_",
                    suffix: str = ".mp3",
                    test=False) -> Path:
    
    if test:
        return AUDIO_FILE

    elevenlabs = ElevenLabs(
    api_key=os.getenv("ELEVENLABS_API_KEY"),
    )

    audio = elevenlabs.text_to_speech.convert(
        text=text_to_read,
        voice_id="JBFqnCBsd6RMkjVDRZzb",
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128"
    )

    file_name = Path(f"{prefix}{time.time()}{suffix}")


    # save mp3 file
    with open(BASE_OUTPUT_PATH / file_name, 'wb') as f:
        for chunk in audio:
            f.write(chunk)

    # speed up audio
    speed_up_audio(BASE_OUTPUT_PATH / file_name, speed_factor)

def speed_up_audio(mp3_file_path: Path, speed_factor: float = 1.25) -> Path:
    """
        Returnes path to .wav file
    """

    # load mp3 and convert to wav
    original_audio = AudioSegment.from_mp3(file=BASE_OUTPUT_PATH / mp3_file_path)
    audio_wav_path = mp3_file_path.with_suffix(".wav")
    original_audio.export(audio_wav_path, format="wav")

    # speed up and return wav
    y, sr = sf.read(audio_wav_path)
    
    # Play back at 1.5X speed
    y_stretch = pyrb.time_stretch(y, sr, speed_factor)
    # Play back two 1.5x tones
    # y_shift = pyrb.pitch_shift(y, sr, 1.5)
    speed_up_wav = Path(f"_{speed_factor}_{audio_wav_path}")
    sf.write(BASE_OUTPUT_PATH / speed_up_wav, y_stretch, sr, format='wav')
    
    

# generate_audio(TEXT)
speed_up_audio(Path("audio_original_1762291021.9402099.mp3"), speed_factor=2.0)



# /Users/szymon/Documents/projekciki/Content_Generation/src/data/audio/audio_original_1762291021.9402099.mp3
