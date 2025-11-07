from pathlib import Path
from schemas.schemas import StoryGenerationOutput, ImagesPromptsOutput

ROOT_SRC = Path(__file__).resolve().parent.parent
BASE_AUDIO_OUTPUT_PATH = ROOT_SRC / "data" / "audio" / "test"

MAIN_TEXT = """"""


AUDIO_FILE = BASE_AUDIO_OUTPUT_PATH / "_2.0_audio_original_1762291021.9402099.wav"
STORY = StoryGenerationOutput(title="Adopting Buster", 
                              text="""Before I adopted Buster, my evenings were quiet. I'd come home from work, make dinner, watch some TV, and maybe read a book. My apartment was always spotless, and my schedule was entirely my own. Then came Buster, a scruffy terrier mix with the biggest, most soulful eyes I'd ever seen. He was a rescue, a bit timid at first, but full of an energy I hadn't anticipated. Now, my evenings are a whirlwind. The moment I walk through the door, I'm greeted by a frantic tail wag and a happy bark. Dinner is often delayed because Buster needs his walk, his playtime, and his endless belly rubs. My apartment? Let's just say 'lived-in' is a generous description, with dog toys scattered like confetti and a fine layer of fur on everything. My schedule revolves around his potty breaks, his feeding times, and ensuring he gets enough exercise. I've learned to appreciate early morning walks, even in the rain, and I've discovered a whole community of dog owners at the local park. There are days I'm exhausted, covered in mud, or frustrated by a chewed-up shoe. But then he'll rest his head on my lap, let out a contented sigh, and look up at me with those big, loving eyes, and I remember why I wouldn't trade this chaotic, fur-filled life for anything. He's not just a pet; he's family, a constant source of joy, laughter, and unconditional love. My life is undeniably messier, but it's also infinitely richer.""",
                              tldr="Adopted - happy")

IMAGE_LINK = """https://wallscloud.net/img/resize/1080/1920/MM/2020-06-14-%D0%9F%D0%B5%D0%B9%D0%B7%D0%B0%D0%B6%2C_%D0%BA%D1%80%D0%B0%D1%81%D0%B8%D0%B2%D0%B0%D1%8F_%D0%BF%D1%80%D0%B8%D1%80%D0%BE%D0%B4%D0%B0%2C_%D0%BB%D0%B5%D1%81%2C_%D0%BD%D0%B5%D0%B1%D0%BE%2C_%D0%B7%D0%B0%D0%BA%D0%B0%D1%82%2C_%D0%B2%D0%BE%D1%81%D1%85%D0%BE%D0%B4%2C_%D0%BE%D0%B7%D0%B5%D1%80%D0%BE.jpg"""
STORY_CHUNKED = [
    ImagesPromptsOutput(
        text="Before I adopted Buster, my evenings were quiet. I'd come home from work, make dinner, watch some TV, and maybe read a book. My apartment was always spotless, and my schedule was entirely my own. Then came Buster, a scruffy terrier mix with the biggest, most soulful eyes I'd ever seen. He was a rescue, a bit timid at first, but full of an energy I hadn't anticipated.",
        img_prompt='A serene, spotless apartment with a person quietly reading a book, contrasted with a scruffy terrier mix with soulful eyes, looking a bit timid but energetic, in a warm, inviting style.'
    ),
    ImagesPromptsOutput(
        text="Now, my evenings are a whirlwind. The moment I walk through the door, I'm greeted by a frantic tail wag and a happy bark. Dinner is often delayed because Buster needs his walk, his playtime, and his endless belly rubs. My apartment? Let's just say 'lived-in' is a generous description, with dog toys scattered like confetti and a fine layer of fur on everything. My schedule revolves around his potty breaks, his feeding times, and ensuring he gets enough exercise.",
        img_prompt="A chaotic but joyful scene: a person being enthusiastically greeted by a dog, dog toys scattered in a 'lived-in' apartment, a person walking a dog, giving belly rubs, showing a busy, dog-centric schedule, in a lively, heartwarming style."
    ),
    ImagesPromptsOutput(
        text="I've learned to appreciate early morning walks, even in the rain, and I've discovered a whole community of dog owners at the local park. There are days I'm exhausted, covered in mud, or frustrated by a chewed-up shoe. But then he'll rest his head on my lap, let out a contented sigh, and look up at me with those big, loving eyes, and I remember why I wouldn't trade this chaotic, fur-filled life for anything. He's not just a pet; he's family, a constant source of joy, laughter, and unconditional love. My life is undeniably messier, but it's also infinitely richer.",
        img_prompt="A person and their dog enjoying an early morning walk in the rain, a vibrant dog park scene, a tired but happy person with a dog resting its head on their lap, a close-up of a dog's loving eyes, conveying unconditional love and a rich, albeit messy, life, in a tender, expressive style."
    )
]
