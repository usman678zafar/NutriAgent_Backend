from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import ssl
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/nutridb")

# Remove ?ssl=require from URL since asyncpg doesn't understand it as a query param.
# We pass ssl=True via connect_args instead.
clean_url = DATABASE_URL.replace("?ssl=require", "").replace("&ssl=require", "")

# Create SSL context for Supabase
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

engine = create_async_engine(
    clean_url,
    echo=True,
    connect_args={
        "ssl": ssl_context,
        "statement_cache_size": 0,  # Required for Supabase transaction-mode pooler
    },
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
