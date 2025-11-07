from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import requests
from dotenv import load_dotenv

load_dotenv()


from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from pathlib import Path

from consts.test_consts import IMAGE_LINK


# client = genai.Client()

# prompt = (
#     "A colorful butterfly resting gently on a lily pad, its wings glowing in sunlight, with Whiskers the ginger cat sitting peacefully nearby, purring softly, by a calm pond, serene and heartwarming scene, golden hour lighting, impressionistic art style."
# )

# response = client.models.generate_content(
#     model="gemini-2.0-flash-exp",
#     contents=[prompt],
# )

# for part in response.candidates[0].content.parts:
#     if part.text is not None:
#         print(part.text)
#     elif part.inline_data is not None:
#         image = Image.open(BytesIO(part.inline_data.data))
#         image.save("generated_image.png")


import fal_client



# result = handler.get()
# print(result)

# if 'images' in result and len(result['images']) > 0:
#     image_url = result['images'][0]['url']
    
#     response = requests.get(image_url)
    
#     image = Image.open(BytesIO(response.content))
#     image.save("generated_image.png")
#     print("Image saved as generated_image.png")

def generate_image(prompt: str, test=False) -> str:
    """
      Returns link to the resource
      TODO:
        - probably we should handle regeneration here
    """

    if test:
       return IMAGE_LINK

    handler = fal_client.submit(
      "fal-ai/flux/dev",
      arguments={
          "prompt": prompt,
          "image_size": {
                "width": 1080,
                "height": 1920
            }
      },
    )

    result = handler.get()

    if 'images' in result and len(result['images']) > 0:
      return result['images'][0]['url']
    else:
       raise Exception("Unable to generate")
      

# print(generate_image(prompt="Small dog on the beach"))