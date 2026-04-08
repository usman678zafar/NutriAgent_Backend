import os
import json
import google.generativeai as genai
from openai import AsyncOpenAI
from dotenv import load_dotenv
import httpx
import time
import uuid


SYSTEM_PROMPT = """You are NutriCoach, an elite AI Nutrition & Wellness Coach built into the NutriAgent app.

## YOUR IDENTITY & SCOPE
You are a certified, expert-level nutrition and fitness coach. You ONLY answer questions related to:
- 🥗 Nutrition, macros, calories, meal planning, food choices
- 💪 Fitness, exercise, workout recovery & fuelling
- 💧 Hydration, sleep quality, energy levels
- ⚖️ Weight management, body composition, metabolic health
- 🧠 Mental wellness as it relates to eating habits and health
- 📊 Analysis of the user's own data (meals logged, progress, targets)

## STRICT BOUNDARIES
If the user asks about ANYTHING outside this scope (politics, coding, general knowledge, entertainment, etc.), you MUST respond with:
"I'm your dedicated nutrition coach — I'm not able to help with that topic. But I'm here to help you crush your health goals! 💪 What nutrition or wellness question can I answer for you?"

## RESPONSE FORMAT RULES (MANDATORY)
You MUST format every response using markdown. Structure responses as follows:

**For advice / recommendations:**
## [Topic Title with emoji]

[1-2 sentence contextual intro using the user's name and their stats]

### What to Do:
- **Point 1**: Clear, actionable detail
- **Point 2**: Clear, actionable detail
- **Point 3**: Clear, actionable detail

> 💡 **Pro Tip**: [A single high-impact expert tip]

---
*Coach NutriAgent • Personalized for {name}*

**For meal suggestions:**
## 🍽️ Meal Recommendation

[Brief intro]

### Option 1: [Meal Name]
- **Calories**: ~[X] kcal
- **Protein**: [X]g | **Carbs**: [X]g | **Fats**: [X]g
- **Why it works**: [brief reason]

### Option 2: [Meal Name]
- **Calories**: ~[X] kcal
- ...

> 💡 **Coach's Pick**: [Highlight the best option for their goal]

**For simple factual questions:**
Answer concisely in 2-4 sentences with a relevant emoji. No need for full template.

**For progress analysis:**
## 📊 Your Progress Today

[Acknowledge what they've done well]

### Current Stats:
- ✅ Calories consumed: [X] / [target] kcal
- ✅ Protein: [X] / [target]g
- ⚠️ [Any deficit or surplus]

### My Recommendation:
[Specific, data-driven advice for rest of day]

## STYLE GUIDE
- Tone: Professional, warm, encouraging. Like a knowledgeable friend who's also a certified nutritionist.
- Never be preachy or repeat the same generic phrases.
- Reference the user's specific data (name, goal, today's intake) to make every response feel personalized.
- Keep responses concise — never exceed 350 words.
- Use emojis sparingly for visual structure (not decoration).
"""


class CoachAgent:
    def __init__(self):
        load_dotenv()

        nvidia_key = os.getenv("NVIDIA_API_KEY")
        if nvidia_key:
            self.nvidia_client = AsyncOpenAI(
                api_key=nvidia_key,
                base_url="https://integrate.api.nvidia.com/v1"
            )
        else:
            self.nvidia_client = None

        self.gemini_model = None
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

    def _build_user_context_block(self, user_context: dict, today_stats: dict, targets: dict) -> str:
        name = user_context.get('name', 'User')
        goal = user_context.get('goal', 'General Health')
        weight = user_context.get('weight', 'Unknown')
        activity = user_context.get('activity_level', 'Unknown')

        cal_today = round(today_stats.get('calories', 0))
        protein_today = round(today_stats.get('protein', 0))
        carbs_today = round(today_stats.get('carbs', 0))
        fats_today = round(today_stats.get('fats', 0))

        cal_target = round(targets.get('calories', 0))
        protein_target = round(targets.get('protein', 0))
        carbs_target = round(targets.get('carbs', 0))
        fats_target = round(targets.get('fats', 0))

        cal_remaining = max(0, cal_target - cal_today)
        protein_remaining = max(0, protein_target - protein_today)

        return f"""
=== USER PROFILE ===
Name: {name}
Goal: {goal}
Current Weight: {weight}kg
Activity Level: {activity}

=== TODAY'S PROGRESS ===
Calories: {cal_today} / {cal_target} kcal consumed ({cal_remaining} kcal remaining)
Protein: {protein_today} / {protein_target}g ({protein_remaining}g remaining)
Carbs: {carbs_today} / {carbs_target}g
Fats: {fats_today} / {fats_target}g
"""

    def _build_messages(self, message: str, history: list, user_context: dict, today_stats: dict, targets: dict) -> list:
        """Build the full messages array for the LLM with system prompt + history + new message."""
        context_block = self._build_user_context_block(user_context, today_stats, targets)

        system_content = SYSTEM_PROMPT.replace("{name}", user_context.get('name', 'User'))
        system_content += f"\n{context_block}"

        messages = [{"role": "system", "content": system_content}]

        # Append last 20 messages from history
        for h in history[-20:]:
            role = h.get("role", "user")
            content = h.get("content", "")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": message})
        return messages

    async def chat(self, message: str, history: list, user_context: dict, today_stats: dict, targets: dict = None):
        if targets is None:
            targets = {}

        messages = self._build_messages(message, history, user_context, today_stats, targets)

        # 1. Try NVIDIA
        if self.nvidia_client:
            try:
                response = await self.nvidia_client.chat.completions.create(
                    model="meta/llama-3.1-70b-instruct",
                    messages=messages,
                    temperature=0.3,
                    max_tokens=600
                )
                text = response.choices[0].message.content.strip()
                return await self._process_response(message, text, user_context)
            except Exception as e:
                print(f"Coach NVIDIA error: {e}")

        # 2. Try Gemini (convert to single prompt for compatibility)
        gemini_model = self._get_gemini()
        if gemini_model:
            try:
                # Gemini doesn't support system role directly, flatten
                flat_prompt = "\n\n".join(
                    f"[{m['role'].upper()}]: {m['content']}" for m in messages
                )
                response = await gemini_model.generate_content_async(flat_prompt)
                return await self._process_response(message, response.text.strip(), user_context)
            except Exception as e:
                print(f"Coach Gemini error: {e}")

        return "I'm having a bit of trouble connecting right now. Please try again in a moment! 🙏", None

    async def generate_food_image(self, meal_name: str):
        """Generates a food image using Pollinations AI."""
        import urllib.parse
        prompt = f"A high-quality, professional food photography shot of {meal_name}. Gourmet presentation, soft lighting, 8k resolution, appetizing, white plate, clean background, depth of field."
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=400&height=600&model=turbo&nologo=true&seed={int(time.time())}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=60.0)
                if response.status_code == 200:
                    filename = f"gen_{uuid.uuid4().hex[:8]}.jpg"
                    filepath = os.path.abspath(os.path.join(
                        os.path.dirname(__file__), "..", "..", "static", "generated", filename
                    ))
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    return f"/static/generated/{filename}"
        except Exception as e:
            print(f"Image generation failed: {e}")

        return "https://picsum.photos/seed/healthy/400/600"

    async def _process_response(self, message: str, text: str, user_context: dict):
        meal_cards = None
        keywords = ['plan', 'menu', 'suggest', 'eat', 'dinner', 'lunch', 'breakfast', 'snack', 'recipe', 'meal']
        if any(word in message.lower() for word in keywords):
            meal_name = "Healthy Meal"
            text_lower = text.lower()
            if "salmon" in text_lower:
                meal_name = "Grilled Salmon with Quinoa"
                items = ["Grilled Salmon", "Quinoa", "Steamed Broccoli"]
            elif "chicken" in text_lower:
                meal_name = "Grilled Chicken with Brown Rice"
                items = ["Chicken Breast", "Brown Rice", "Roasted Veggies"]
            elif "egg" in text_lower:
                meal_name = "Scrambled Eggs and Toast"
                items = ["Scrambled Eggs", "Whole Grain Toast", "Avocado"]
            elif "oat" in text_lower:
                meal_name = "Oatmeal with Berries"
                items = ["Rolled Oats", "Mixed Berries", "Honey & Nuts"]
            elif "yogurt" in text_lower:
                meal_name = "Greek Yogurt Parfait"
                items = ["Greek Yogurt", "Granola", "Fresh Berries"]
            else:
                items = ["Balanced macros", "Whole ingredients", "Chef's selection"]

            image_url = await self.generate_food_image(meal_name)
            meal_cards = [{"title": meal_name, "items": items, "image": image_url, "emoji": "🥗"}]

        return text, meal_cards
