"""Database connection and session management"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from loguru import logger
from dotenv import load_dotenv

from .models import Base

load_dotenv()


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self, database_url: str = None):
        """
        Initialize database manager
        
        Args:
            database_url: PostgreSQL connection string
                         Format: postgresql://user:password@host:port/database
        """
        self.database_url = database_url or os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:postgres@localhost:5432/amazon_deals'
        )
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            echo=False  # Set to True for SQL query logging
        )
        
        # Create session factory
        self.SessionLocal = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        )
        
        logger.info(f"✅ Database manager initialized")
    
    def create_tables(self):
        """Create all tables in the database"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.success("✅ Database tables created successfully")
        except Exception as e:
            logger.error(f"❌ Error creating tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("⚠️ All database tables dropped")
        except Exception as e:
            logger.error(f"❌ Error dropping tables: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """
        Context manager for database sessions
        
        Usage:
            with db_manager.get_session() as session:
                session.query(Product).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Session error: {e}")
            raise
        finally:
            session.close()
    
    def close(self):
        """Close all database connections"""
        self.SessionLocal.remove()
        self.engine.dispose()
        logger.info("🔒 Database connections closed")
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")
            logger.success("✅ Database connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


def init_database(database_url: str = None):
    """Initialize database and create tables"""
    global db_manager
    db_manager = DatabaseManager(database_url)
    db_manager.create_tables()
    return db_manager


def get_db_session():
    """Get database session (for dependency injection)"""
    return db_manager.get_session()
