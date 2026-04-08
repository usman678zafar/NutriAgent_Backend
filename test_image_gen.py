import asyncio
import os
import httpx
from dotenv import load_dotenv
from app.agents.coach_agent import CoachAgent

async def test_image_gen():
    load_dotenv()
    coach = CoachAgent()
    
    print("Testing Image Generation for 'Grilled Salmon'...")
    try:
        image_url = await coach.generate_food_image("Grilled Salmon with Quinoa")
    except Exception as e:
        print(f"Test caught exception: {e}")
        image_url = None
        
    print(f"Generated Image URL: {image_url}")
    
    if image_url.startswith("/static"):
        filepath = os.path.join(os.path.dirname(__file__), image_url.lstrip("/"))
        if os.path.exists(filepath):
            print(f"SUCCESS: Image exists at {filepath}")
            print(f"Size: {os.path.getsize(filepath)} bytes")
        else:
            print(f"FAILURE: Image NOT found at {filepath}")
    else:
        print("Fallback URL returned (likely API key horizontal or error).")

if __name__ == "__main__":
    asyncio.run(test_image_gen())
