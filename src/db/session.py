from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.config.settings import get_settings

settings = get_settings()
DATABASE_URL = settings.database_url

# Convert to async driver if PostgreSQL
if DATABASE_URL.startswith("postgresql://") and "asyncpg" not in DATABASE_URL:
    async_db_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    async_db_url = DATABASE_URL

engine = create_async_engine(async_db_url, future=True, echo=False)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db():
    """Yield an async SQLAlchemy session."""
    async with AsyncSessionLocal() as session:
        yield session
