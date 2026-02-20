from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

try:
    engine = create_async_engine(settings.database_url, future=True, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
except ModuleNotFoundError:
    engine = None
    SessionLocal = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if SessionLocal is None:
        raise RuntimeError("Database driver is not installed. Install requirements.txt dependencies.")
    async with SessionLocal() as session:
        yield session
