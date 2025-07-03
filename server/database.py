"""
SUBFRACTURE Database Service

Database operations and connection management for FastMCP server
"""

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dynaconf import Dynaconf
from models import Base

# Load configuration
config = Dynaconf(
    envvar_prefix="SUBFRACTURE",
    settings_files=["config/settings.toml", "config/.secrets.toml"],
    environments=True,
    load_dotenv=True,
)

class DatabaseService:
    """Database operations service"""
    
    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            echo=config.get("db_echo", False),
            pool_size=config.get("db_pool_size", 20),
            max_overflow=config.get("db_max_overflow", 30),
            pool_timeout=config.get("db_pool_timeout", 30),
            pool_recycle=config.get("db_pool_recycle", 3600),
        )
        self.SessionLocal = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def init_db(self):
        """Initialize database tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self):
        """Close database connections"""
        await self.engine.dispose()
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with automatic cleanup"""
        async with self.SessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()