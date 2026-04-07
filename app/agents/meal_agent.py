import random
import os
import json
import google.generativeai as genai

class MealAgent:
    def __init__(self):
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
        
        # Initialize Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "your_gemini_api_key_here":
            genai.configure(api_key=api_key)
            # Use flash for speed
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    async def estimate_nutrients(self, food_query: str):
        """
        AI Agent reasoning: 
        1. Try LLM for global knowledge.
        2. Fallback to Local Knowledge Base.
        3. Fallback to Heuristic Default.
        """
        if self.model:
            prompt = f"""
            Analyze the following food item or meal description and provide its estimated nutritional data (per standard serving).
            Return the result ONLY as a JSON object with these keys: 
            "food_name", "calories", "protein", "carbs", "fats".
            Ensure all values are numbers (integers where possible).
            
            Food: {food_query}
            """
            try:
                response = await self.model.generate_content_async(prompt)
                text = response.text.strip()
                # Clean up JSON formatting if present
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                
                data = json.loads(text)
                return {
                    "food_name": data.get("food_name", food_query.capitalize()),
                    "calories": float(data.get("calories", 0)),
                    "protein": float(data.get("protein", 0)),
                    "carbs": float(data.get("carbs", 0)),
                    "fats": float(data.get("fats", 0))
                }
            except Exception as e:
                print(f"Gemini estimation failed: {e}")

        # Fallback to local Expert Database
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
        
        # Final Heuristic Fallback
        return {
            "food_name": food_query.capitalize(),
            "calories": 350,
            "protein": 20,
            "carbs": 40,
            "fats": 10
        }

    async def scan_food_image(self, base64_image: str):
        """
        Uses Gemini Vision to identify food and estimate nutrients from an image.
        """
        if not self.model:
            return None
            
        prompt = """
        Identify the food in this image and provide estimated nutritional data for the entire meal shown.
        Return the result ONLY as a JSON object with these keys: 
        "food_name", "calories", "protein", "carbs", "fats", "description".
        "description" should be a 1-sentence analysis of the meal's healthiness.
        Ensure all nutritional values are numbers.
        """
        
        try:
            # Prepare image for Gemini
            import base64
            image_data = base64.b64decode(base64_image.split(",")[-1])
            
            contents = [
                prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ]
            
            response = await self.model.generate_content_async(contents)
            text = response.text.strip()
            
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            return data
        except Exception as e:
            print(f"Gemini image scan failed: {e}")
            return None

    def generate_meal_plan(self, target_calories, target_protein, target_carbs, target_fats):
        plan = []
        for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
            meal = random.choice(self.meal_database[meal_type])
            calories = meal.get("calories", meal["protein"]*4 + meal["carbs"]*4 + meal["fats"]*9)
            plan.append({
                "meal_type": meal_type,
                "food_name": meal["name"],
                "calories": round(calories),
                "protein": meal["protein"],
                "carbs": meal["carbs"],
                "fats": meal["fats"]
            })
        
        return plan
