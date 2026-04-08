import asyncio
import os
import ssl
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

# Load env from backend directory
load_dotenv('e:/NutriAgent/backend/.env')

DATABASE_URL = os.getenv("DATABASE_URL")
clean_url = DATABASE_URL.replace("?ssl=require", "").replace("&ssl=require", "")

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

engine = create_async_engine(
    clean_url,
    connect_args={
        "ssl": ssl_context,
    },
)

async def migrate():
    async with engine.begin() as conn:
        print("Checking for target_weight column in body_metrics...")
        try:
            await conn.execute(text("ALTER TABLE body_metrics ADD COLUMN IF NOT EXISTS target_weight FLOAT"))
            print("Successfully added target_weight column to body_metrics table.")
        except Exception as e:
            print(f"Error migrating: {e}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
