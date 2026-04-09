
import asyncio
from sqlalchemy import text
from app.db.database import engine

async def migrate():
    async with engine.begin() as conn:
        print("Adding 'volume' column to 'meals' table...")
        try:
            await conn.execute(text("ALTER TABLE meals ADD COLUMN volume FLOAT DEFAULT 0"))
            print("Successfully added 'volume' column.")
        except Exception as e:
            print(f"Error adding 'volume': {e}")
            
        print("Adding 'source' column to 'meals' table...")
        try:
            await conn.execute(text("ALTER TABLE meals ADD COLUMN source VARCHAR DEFAULT 'manual'"))
            print("Successfully added 'source' column.")
        except Exception as e:
            print(f"Error adding 'source': {e}")

if __name__ == "__main__":
    asyncio.run(migrate())
