import asyncio
from app.db.database import engine
from sqlalchemy import text

async def test_db():
    print("Testing DB connection...")
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(f"DB Success: {result.scalar()}")
    except Exception as e:
        print(f"DB Failure: {e}")

if __name__ == "__main__":
    asyncio.run(test_db())
