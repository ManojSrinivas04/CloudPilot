from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.app.config import settings

Base = declarative_base()

# Determine database engine parameters
db_url = settings.DATABASE_URL

if not db_url.startswith("postgresql+psycopg2://"):
    raise ValueError(
        "DATABASE_URL must use postgresql+psycopg2; "
        "SQLite is supported only through explicit test dependency overrides."
    )

engine = create_engine(db_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency to yield a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initializes database tables, propagating connection or schema errors."""
    Base.metadata.create_all(bind=engine)
