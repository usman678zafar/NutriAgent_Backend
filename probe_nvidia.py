import os
import httpx
import asyncio
from dotenv import load_dotenv

async def probe_endpoints():
    load_dotenv()
    api_key = os.getenv("NVIDIA_API_KEY")
    
    endpoints = [
        "https://ai.api.nvidia.com/v1/genai/stabilityai/sdxl-turbo",
        "https://ai.api.nvidia.com/v1/visual/stabilityai/sdxl-turbo",
        "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-xl",
        "https://ai.api.nvidia.com/v1/visual/black-forest-labs/flux-1-schnell",
        "https://ai.api.nvidia.com/v1/genai/nvidia/playground-sdxl"
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    print("Probing endpoints...")
    for url in endpoints:
        try:
            # We use a GET or an empty POST to check for 404 vs 401/405/200
            response = await httpx.post(url, headers=headers, json={}, timeout=5.0)
            print(f"URL: {url} -> Status: {response.status_code}")
        except Exception as e:
            print(f"URL: {url} -> Error: {e}")

if __name__ == "__main__":
    asyncio.run(probe_endpoints())
