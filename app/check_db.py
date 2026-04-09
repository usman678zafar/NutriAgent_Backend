
import asyncio
import uuid
from sqlalchemy.future import select
from app.db.database import AsyncSessionLocal
from app.models.models import Meal

async def check_meals():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Meal))
        meals = result.scalars().all()
        print(f"Total meals: {len(meals)}")
        for m in meals:
            print(f"ID: {m.id}, User: {m.user_id}, Name: {m.food_name}, Type: {m.meal_type}, Cal: {m.calories}, Pro: {m.protein}, Carb: {m.carbs}, Fat: {m.fats}, Vol: {m.volume}, Date: {m.timestamp}")
            if m.calories is None or m.protein is None or m.carbs is None or m.fats is None:
                print(f"!!! NULL value found in meal {m.id}")

if __name__ == "__main__":
    asyncio.run(check_meals())
