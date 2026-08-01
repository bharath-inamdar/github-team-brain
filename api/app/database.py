from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.database_url,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    """
    Creates one database session for each request.
    The session is automatically closed after the request finishes.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


from app.models import Base


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
