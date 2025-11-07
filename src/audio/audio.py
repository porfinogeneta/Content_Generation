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

load_dotenv()



def generate_audio(text_to_read: str,
                    title: str,
                    speed_factor: float = 1.25,
                    prefix: str = "audio_original_",
                    suffix: str = ".mp3",
                    test=False) -> Path:
    
    """
        
    """
    
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
    


    ROOT_SRC = Path(__file__).resolve().parent.parent
    BASE_OUTPUT_PATH = ROOT_SRC / "data" / "audio"
    
    OUTPUT_MAIN_PATH = BASE_OUTPUT_PATH / title
    OUTPUT_MAIN_PATH.mkdir(parents=True, exist_ok=True)

    mp3_file_path = OUTPUT_MAIN_PATH / Path(f"{prefix}{time.time()}{suffix}")

    # save mp3 file
    try:
        with open(mp3_file_path, 'wb') as f:
            for chunk in audio:
                f.write(chunk)
    except:
        raise Exception("Unable tp create audio!")
    finally:
        if mp3_file_path.exists():
            mp3_file_path.unlink()


    # speed up audio
    return speed_up_audio(mp3_file_path, speed_factor)
    
def speed_up_audio(mp3_file_path: Path, speed_factor: float = 1.25) -> Path:
    """
        Returnes path to .wav file
    """

    # load mp3 and convert to wav
    original_audio = AudioSegment.from_mp3(file=mp3_file_path)
    
    with tempfile.TemporaryFile() as temp_file:
        # audio_wav_path = mp3_file_path.with_suffix(".wav")
        original_audio.export(temp_file, format="wav")

        # put file pointer at the beginning
        temp_file.seek(0)

        # speed up and return wav
        y, sr = sf.read(temp_file)
        
        # Play back at 1.5X speed
        y_stretch = pyrb.time_stretch(y, sr, speed_factor)
        # Play back two 1.5x tones
        # y_shift = pyrb.pitch_shift(y, sr, 1.5)

        mp3_file_name = Path(mp3_file_path.name)
        mp3_file_parent_folder = mp3_file_path.parent

        speed_up_file_name = mp3_file_name.with_suffix(".wav")

        speed_up_wav = Path(f"_{speed_factor}_{speed_up_file_name}")
        SPEED_UP_WAV_FULL_PATH = mp3_file_parent_folder / speed_up_wav
        sf.write(SPEED_UP_WAV_FULL_PATH, y_stretch, sr, format='wav')

    
    return SPEED_UP_WAV_FULL_PATH
    

# generate_audio(text_to_read="Before I adopted Buster, my evenings were quiet. I'd come home from work, make dinner, watch some TV, and maybe read a book. My apartment was always spotless, and my schedule was entirely my own. Then came Buster, a scruffy terrier mix with the biggest, most soulful eyes I'd ever seen. He was a rescue, a bit timid at first, but full of an energy I hadn't anticipated.",
#                title="test")
# speed_up_audio(Path("audio_original_1762291021.9402099.mp3"), speed_factor=2.0)



# /Users/szymon/Documents/projekciki/Content_Generation/src/data/audio/audio_original_1762291021.9402099.mp3
