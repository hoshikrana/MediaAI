import asyncio
from backend.db.session import engine
from backend.db.base import Base
# Import all models to ensure they are registered with Base metadata
import backend.db.models

async def init_db():
    print("Initializing Database...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database Initialized!")

if __name__ == "__main__":
    asyncio.run(init_db())




