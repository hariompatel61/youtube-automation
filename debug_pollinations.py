import requests
from urllib.parse import quote
import random

def test_pollinations():
    prompt = "High quality 3D render of a dog astronaut on the moon. Style: Disney Pixar."
    width = 1080
    height = 1920
    model = "flux"
    seed = 42
    
    encoded_prompt = quote(prompt)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    variations = [
        ("JSON endpoint", f"https://pollinations.ai/prompt/{encoded_prompt}?json=true"),
        ("JSON endpoint + Flux", f"https://pollinations.ai/prompt/{encoded_prompt}?model=flux&json=true"),
        ("No Model Param", f"https://image.pollinations.ai/prompt/{encoded_prompt}"),
    ]
    
    for name, url in variations:
        print(f"Testing {name}: {url}")
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            print(f"Status: {resp.status_code}")
            print(f"Content-Type: {resp.headers.get('Content-Type')}")
            print(f"Text: {resp.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 20)

if __name__ == "__main__":
    test_pollinations()
