from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from ..models.CoCoConfig import CoCoConfig

Base = declarative_base()

def get_db(config: CoCoConfig):

    engine = create_engine(config.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
