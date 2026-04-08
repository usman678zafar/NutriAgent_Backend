import os
import requests
from dotenv import load_dotenv

def list_image_models():
    load_dotenv()
    api_key = os.getenv("NVIDIA_API_KEY")
    url = "https://ai.api.nvidia.com/v1/genai/models" # Common discovery endpoint
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            models = response.json()
            print("Available Models:")
            for m in models.get("data", []):
                print(f"- {m.get('id')}")
        else:
            print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Failed to list models: {e}")

if __name__ == "__main__":
    list_image_models()
