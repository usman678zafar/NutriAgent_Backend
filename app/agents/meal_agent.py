import random
import os
import json
import google.generativeai as genai
from openai import AsyncOpenAI
import base64
from dotenv import load_dotenv

class MealAgent:
    def __init__(self):
        load_dotenv()
        self.meal_database = {
            "breakfast": [
                {"name": "Oatmeal with protein powder and berries", "protein": 30, "carbs": 50, "fats": 8},
                {"name": "Scrambled eggs with spinach and whole-grain toast", "protein": 25, "carbs": 30, "fats": 15},
                {"name": "Greek yogurt parfait with nuts and honey", "protein": 20, "carbs": 25, "fats": 12}
            ],
            "lunch": [
                {"name": "Grilled chicken salad with avocado", "protein": 35, "carbs": 10, "fats": 18},
                {"name": "Turkey sandwich on whole wheat wrap", "protein": 30, "carbs": 40, "fats": 10},
                {"name": "Quinoa bowl with chickpeas and roasted veggies", "protein": 15, "carbs": 60, "fats": 12}
            ],
            "dinner": [
                {"name": "Baked salmon with asparagus and quinoa", "protein": 30, "carbs": 35, "fats": 20},
                {"name": "Lean beef stir-fry with broccoli and brown rice", "protein": 35, "carbs": 45, "fats": 12},
                {"name": "Lentil soup with a side of steamed veggies", "protein": 18, "carbs": 55, "fats": 5}
            ],
            "snack": [
                {"name": "Apple with almond butter", "protein": 4, "carbs": 25, "fats": 9},
                {"name": "Cottage cheese with pineapple", "protein": 15, "carbs": 15, "fats": 2},
                {"name": "Handful of almonds and a protein shake", "protein": 30, "carbs": 5, "fats": 14}
            ]
        }
        
        # Initialize NVIDIA
        nvidia_key = os.getenv("NVIDIA_API_KEY")
        if nvidia_key:
            self.nvidia_client = AsyncOpenAI(
                api_key=nvidia_key,
                base_url="https://integrate.api.nvidia.com/v1"
            )
        else:
            self.nvidia_client = None

        # Initialize Gemini Fallback
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key and gemini_key != "your_gemini_api_key_here":
            genai.configure(api_key=gemini_key)
            # Use flash for speed
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.gemini_model = None

    async def estimate_nutrients(self, food_query: str):
        """
        AI Agent reasoning: 
        1. Validate input.
        2. Check for basic items like water first.
        3. Try NVIDIA LLM for global knowledge.
        4. Fallback to Gemini LLM.
        5. Fallback to Local Knowledge Base.
        6. Fallback to Safe Default (0 for unknown).
        """
        # 0. Input validation
        if not food_query or not isinstance(food_query, str):
            raise ValueError("food_query must be a non-empty string")
        food_query = food_query.strip()
        if len(food_query) > 500:
            raise ValueError("food_query is too long (max 500 characters)")
        if len(food_query) < 2:
            raise ValueError("food_query is too short — please describe the food")

        # 1. Quick detection for zero-calorie common items
        food_lower = food_query.lower()
        if any(word in food_lower for word in ["water", "black coffee", "plain tea"]):
            return {
                "food_name": food_query.capitalize(),
                "calories": 0,
                "protein": 0,
                "carbs": 0,
                "fats": 0
            }

        prompt = f"""
        Analyze the following food item or meal description and provide its estimated nutritional data (per standard serving).
        Return the result ONLY as a JSON object with these keys: 
        "food_name", "calories", "protein", "carbs", "fats".
        Ensure all values are numbers (integers where possible).
        
        Food: {food_query}
        """

        # 1. Try NVIDIA
        if self.nvidia_client:
            try:
                response = await self.nvidia_client.chat.completions.create(
                    model="meta/llama-3.1-70b-instruct",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=200
                )
                text = response.choices[0].message.content.strip()
                return self._parse_json_response(text, food_query)
            except Exception as e:
                print(f"NVIDIA estimation failed: {e}")

        # 2. Try Gemini
        if self.gemini_model:
            try:
                response = await self.gemini_model.generate_content_async(prompt)
                text = response.text.strip()
                return self._parse_json_response(text, food_query)
            except Exception as e:
                print(f"Gemini estimation failed: {e}")

        # 3. Fallback to local Expert Database
        food_lower = food_query.lower()
        all_meals = []
        for cat in self.meal_database.values():
            all_meals.extend(cat)
            
        for meal in all_meals:
            if any(word in meal["name"].lower() for word in food_lower.split() if len(word) > 2):
                return {
                    "food_name": meal["name"],
                    "calories": meal.get("calories", meal["protein"]*4 + meal["carbs"]*4 + meal["fats"]*9),
                    "protein": meal["protein"],
                    "carbs": meal["carbs"],
                    "fats": meal["fats"]
                }
        
        # 5. Final Safe Fallback (Return 0 to avoid misleading the user)
        return {
            "food_name": food_query.capitalize(),
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fats": 0
        }

    def _parse_json_response(self, text, default_name):
        """Parse JSON from LLM response with graceful fallback."""
        try:
            # Clean up fenced code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()

            # Some models wrap with extra prose — extract the JSON object
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                text = text[start:end + 1]

            data = json.loads(text)
            return {
                "food_name": str(data.get("food_name", default_name)).capitalize(),
                "calories": float(data.get("calories", 0)),
                "protein":  float(data.get("protein",  0)),
                "carbs":    float(data.get("carbs",    0)),
                "fats":     float(data.get("fats",     0)),
            }
        except Exception as e:
            print(f"JSON parse error: {e} | raw text: {text[:200]}")
            return None   # caller will fall through to next strategy

    async def scan_food_image(self, base64_image: str):
        """
        Uses NVIDIA Vision (fallback to Gemini) to identify food and estimate nutrients from an image.
        """
        prompt = """
        Identify the food in this image and provide estimated nutritional data for the entire meal shown.
        Return the result ONLY as a JSON object with these keys: 
        "food_name", "calories", "protein", "carbs", "fats", "description".
        "description" should be a 1-sentence analysis of the meal's healthiness.
        Ensure all nutritional values are numbers.
        """

        # 1. Try NVIDIA Multimodal
        if self.nvidia_client:
            try:
                # Need the data URI scheme for NVIDIA (openai spec)
                image_url = base64_image if base64_image.startswith("data:image") else f"data:image/jpeg;base64,{base64_image.split(',')[-1]}"
                response = await self.nvidia_client.chat.completions.create(
                    model="meta/llama-3.2-90b-vision-instruct",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }],
                    temperature=0.2,
                    max_tokens=300
                )
                text = response.choices[0].message.content.strip()
                return self._parse_json_image_response(text)
            except Exception as e:
                print(f"NVIDIA image scan failed: {e}")

        # 2. Try Gemini
        if self.gemini_model:
            try:
                image_data = base64.b64decode(base64_image.split(",")[-1])
                contents = [
                    prompt,
                    {"mime_type": "image/jpeg", "data": image_data}
                ]
                
                response = await self.gemini_model.generate_content_async(contents)
                text = response.text.strip()
                return self._parse_json_image_response(text)
            except Exception as e:
                print(f"Gemini image scan failed: {e}")

        return None

    def _parse_json_image_response(self, text):
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        data = json.loads(text)
        return data

    def generate_meal_plan(self, target_calories, target_protein, target_carbs, target_fats):
        """
        Select meals that are closest to the per-meal macro budget.
        Each meal type gets an equal share of the daily calorie target.
        Best-fit is chosen by minimising the normalised Euclidean distance
        to the per-meal budget in (protein, carbs, fats) space.
        """
        meal_types = ["breakfast", "lunch", "dinner", "snack"]
        # Each meal gets roughly equal share (snack gets half)
        weights = {"breakfast": 0.3, "lunch": 0.35, "dinner": 0.3, "snack": 0.05}

        plan = []
        for meal_type in meal_types:
            w = weights[meal_type]
            budget_protein = target_protein * w
            budget_carbs   = target_carbs   * w
            budget_fats    = target_fats    * w

            candidates = self.meal_database[meal_type]

            def score(meal):
                dp = (meal["protein"] - budget_protein) ** 2
                dc = (meal["carbs"]   - budget_carbs)   ** 2
                df = (meal["fats"]    - budget_fats)    ** 2
                return dp + dc + df

            best = min(candidates, key=score)
            calories = best.get(
                "calories",
                best["protein"] * 4 + best["carbs"] * 4 + best["fats"] * 9
            )
            plan.append({
                "meal_type": meal_type,
                "food_name": best["name"],
                "calories":  round(calories),
                "protein":   best["protein"],
                "carbs":     best["carbs"],
                "fats":      best["fats"],
            })

        return plan
