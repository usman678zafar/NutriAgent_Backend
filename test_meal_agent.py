import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.agents.meal_agent import MealAgent

async def test():
    agent = MealAgent()
    res = await agent.estimate_nutrients("A bowl of ramen with pork slices and an egg")
    print("Estimation:", res)

if __name__ == "__main__":
    asyncio.run(test())
