from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session
from .db import Base

from models.CoCoConfig import CoCoConfig

def get_db(config: CoCoConfig):

    engine = create_engine(config.database_url)
    SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

    db = SessionLocal()

    return db
