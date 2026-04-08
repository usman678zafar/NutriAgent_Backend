import asyncio
from app.db.database import AsyncSessionLocal
from app.models.models import User
from sqlalchemy import select

async def test_user_query():
    print("Testing User query...")
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).limit(1))
            user = result.scalars().first()
            print(f"User Query Success: {user.name if user else 'No users'}")
    except Exception as e:
        print(f"User Query Failure: {e}")

if __name__ == "__main__":
    asyncio.run(test_user_query())
