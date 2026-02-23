import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def test_gemini_image():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ No GEMINI_API_KEY found in .env")
        return

    print(f"Testing with API Key: {api_key[:10]}...")
    
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = "High quality 3D render of a cute robot cat. Style: Disney Pixar."
        print(f"Generating image for: '{prompt}'")
        
        # Test Imagen 3
        try:
            response = client.models.generate_images(
                model='imagen-3.0-generate-001',
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio="9:16"
                )
            )
            
            if response.generated_images:
                img_data = response.generated_images[0].image.image_bytes
                with open("test_gemini_3d.png", "wb") as f:
                    f.write(img_data)
                print("Success! Saved test_gemini_3d.png")
                return
            else:
                print("Warning: No images returned.")
                
        except Exception as e:
            print(f"Error: Imagen 3 failed: {e}")

        # Fallback to older model if available or different name?
        # Typically 'imagen-3.0-generate-001' is the current public beta one.

    except Exception as e:
        print(f"Error: Client initialization failed: {e}")

if __name__ == "__main__":
    test_gemini_image()
