import os
import json
import google.generativeai as genai
from openai import AsyncOpenAI
from dotenv import load_dotenv
import httpx
import base64
import time
import uuid

class CoachAgent:
    def __init__(self):
        load_dotenv()
        
        # Initialize NVIDIA (Primary for this key set)
        nvidia_key = os.getenv("NVIDIA_API_KEY")
        if nvidia_key:
            self.nvidia_client = AsyncOpenAI(
                api_key=nvidia_key,
                base_url="https://integrate.api.nvidia.com/v1"
            )
        else:
            self.nvidia_client = None

        # Lazy load Gemini to prevent startup hangs
        self.gemini_model = None
        self.base_url = "http://localhost:8000"
        self.image_gen_url = "https://ai.api.nvidia.com/v1/genai/stabilityai/sdxl-turbo"
        self.nvidia_key = nvidia_key

    def _get_gemini(self):
        if self.gemini_model:
            return self.gemini_model
        
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                genai.configure(api_key=gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                return self.gemini_model
            except Exception as e:
                print(f"Gemini init error: {e}")
        return None

    async def chat(self, message: str, history: list, user_context: dict, today_stats: dict):
        prompt = f"""
        Analyze the conversation and respond as NutriAgent.
        
        SYSTEM CONTEXT:
        User Goal: {user_context.get('goal', 'General Health')}
        Name: {user_context.get('name', 'User')}
        Weight: {user_context.get('weight', 'Unknown')}kg
        Progress today: {today_stats.get('calories', 0)}kcal, {today_stats.get('protein', 0)}g protein, {today_stats.get('water', 0)}ml water.
        
        CONVERSATION HISTORY:
        {json.dumps(history, indent=2)}
        
        NEW MESSAGE:
        {message}
        
        Be concise, professional, and encouraging.
        """

        # 1. Try NVIDIA
        if self.nvidia_client:
            try:
                response = await self.nvidia_client.chat.completions.create(
                    model="meta/llama-3.1-70b-instruct",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=500
                )
                text = response.choices[0].message.content.strip()
                return await self._process_response(message, text, user_context)
            except Exception as e:
                print(f"Coach NVIDIA error: {e}")

        # 2. Try Gemini
        gemini_model = self._get_gemini()
        if gemini_model:
            try:
                response = await gemini_model.generate_content_async(prompt)
                return await self._process_response(message, response.text.strip(), user_context)
            except Exception as e:
                print(f"Coach Gemini error: {e}")

        return "I'm having a bit of trouble connecting to my brain right now. Please try again!", None

    async def generate_food_image(self, meal_name: str):
        """
        Generates a food image using Pollinations AI (Free FLUX/Stable Diffusion).
        """
        # Create a descriptive prompt for better quality
        prompt = f"A high-quality, professional food photography shot of {meal_name}. Gourmet presentation, soft lighting, 8k resolution, appetizing, white plate, clean background, depth of field."
        
        # Pollinations AI uses a simple GET request for images
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        # Use 'turbo' model for faster results as requested for a 'free model' experience
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=400&height=600&model=turbo&nologo=true&seed={int(time.time())}"
        
        print(f"Calling Pollinations: {url}")

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=60.0)
                
                if response.status_code == 200:
                    # Save to static/generated
                    filename = f"gen_{uuid.uuid4().hex[:8]}.jpg"
                    filepath = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static", "generated", filename))
                    
                    print(f"Saving image to: {filepath}")
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    
                    return f"/static/generated/{filename}"
                else:
                    print(f"Image Gen API Error: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            import traceback
            print(f"Image generation failed: {e}")
            traceback.print_exc()
            
        return "https://picsum.photos/seed/healthy/400/600"

    async def _process_response(self, message: str, text: str, user_context: dict):
        meal_cards = None
        # Improved detection: if the AI suggests a meal or uses words like "suggest", "plan"
        if any(word in message.lower() for word in ['plan', 'menu', 'suggest', 'eat', 'dinner', 'lunch', 'breakfast', 'snack']):
            # 1. Identify what the meal is. We can ask the AI briefly or just use a default based on text
            # For simplicity, if "Salmon" is in the text, use that.
            meal_name = "Healthy Meal"
            if "salmon" in text.lower(): meal_name = "Grilled Salmon with Quinoa"
            elif "chicken" in text.lower(): meal_name = "Grilled Chicken with Brown Rice"
            elif "egg" in text.lower(): meal_name = "Scrambled Eggs and Toast"
            elif "oat" in text.lower(): meal_name = "Oatmeal with Berries"
            elif "yogurt" in text.lower(): meal_name = "Greek Yogurt Parfait"
            
            # 2. Generate the image
            image_url = await self.generate_food_image(meal_name)
            
            # Extract ingredients/items from text if possible (simplified)
            items = ["High-quality ingredients", "Balanced macros", "Chef's selection"]
            if "salmon" in text.lower(): items = ["Grilled Salmon", "Quinoa", "Steamed Broccoli"]
            elif "chicken" in text.lower(): items = ["Chicken Breast", "Brown Rice", "Roasted Veggies"]
            
            meal_cards = [
                {
                    "title": meal_name,
                    "items": items,
                    "image": image_url,
                    "emoji": "🥗"
                }
            ]
            
        return text, meal_cards
