from ollama_client import OllamaClient
import ollama
from ollama import generate

import glob
import pandas as pd
from PIL import Image

import os
from io import BytesIO


import requests
import json
import os
import glob
import pandas as pd
import base64
from PIL import Image
from io import BytesIO
from typing import Optional

class OllamaImageProcessor(OllamaClient):
    """
    A class to perform image processing using Ollama's multimodal models.
    """
    def __init__(self):
        super().__init__()
    

    def _image_to_base64(self, image_path: str) -> str:
        """Converts an image file to a base64 encoded string."""
        with Image.open(image_path) as img:
            # Convert image to RGB to handle various input formats (RGBA, P, etc.)
            if img.mode not in ('RGB', 'L'): # L for grayscale, but RGB is more common for LLMs
                img = img.convert('RGB')
            with BytesIO() as buffer:
                # Save as JPEG for potentially smaller size, or PNG if exact format needed
                img.save(buffer, format='JPEG')
                return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def get_image_annotation(self, image_path: str, prompt: str=None) -> Optional[str]:
        """
        Annotates a single image using the configured Ollama model.

        Args:
            image_path (str): The file path to the image.
            prompt (str): The text prompt for the annotation.

        Returns:
            Optional[str]: The generated image annotation string, or None if an error occurs.
        """

        if prompt is None:
            prompt = "Describe this image in detail, focusing on key objects, actions, and any visible text. Be concise but comprehensive."

        try:
            image_base64_data = self._image_to_base64(image_path)
            payload,generate_endpoint = super().image_payload(prompt, file_path=image_base64_data,stream=True)
            headers = {"Content-Type": "application/json"}

            response = requests.post(generate_endpoint, headers=headers, data=json.dumps(payload), timeout=180)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

            return response.json().get('response')

        except FileNotFoundError:
            print(f"Error: Image file not found at '{image_path}'")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error calling Ollama API for '{image_path}': {e}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred processing '{image_path}': {e}")
            return None

    def generate_text(instruction, file_path):
        result = ollama.generate(
            model='llava',
            prompt=instruction,
            images=[file_path],
            stream=False
        )['response']
        img=Image.open(file_path, mode='r')
        img = img.resize([int(i/1.2) for i in img.size])
        
        for i in result.split('.'):
            print(i, end='', flush=True)
            

# --- Example Usage ---
if __name__ == "__main__":
    
    # Initialize the annotator
    annotator = OllamaImageProcessor()

    # --- Use Case 1: Annotate a single image ---
    print("--- Single Image Annotation Example ---")
    # Replace with an actual image path from the examples/assets folder.
    single_image_path = "examples/assets/1747406638073.jpg"

    if os.path.exists(single_image_path):
        single_annotation = annotator.get_image_annotation(single_image_path, "What is in this image?")
        if single_annotation:
            print(f"\nAnnotation for '{single_image_path}':")
            print(single_annotation)
        else:
            print(f"\nCould not annotate '{single_image_path}'.")
    else:
        print("\nSkipping single image annotation example as no test image is available.")

    print("\n" + "="*50 + "\n")

    

    
# # processing the images 
# def process_image(image_file):
#     print(f"\nProcessing {image_file}\n")
#     with Image.open(image_file) as img:
#         with BytesIO() as buffer:
#             img.save(buffer, format='PNG')
#             image_bytes = buffer.getvalue()

#     full_response = ''
#     # Generate a description of the image
#     for response in generate(model='llava:13b-v1.6', 
#                              prompt='describe this image and make sure to include anything notable about it (include text you see in the image):', 
#                              images=[image_bytes], 
#                              stream=True):
#         # Print the response to the console and add it to the full response
#         print(response['response'], end='', flush=True)
#         full_response += response['response']

#     # Add a new row to the DataFrame
#     df.loc[len(df)] = [image_file, full_response]


# for image_file in image_files:
#     if image_file not in df['image_file'].values:
#         process_image(image_file)

# # Save the DataFrame to a CSV file
# df.to_csv('image_descriptions.csv', index=False)

