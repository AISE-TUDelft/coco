from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from models.CoCoConfig import CoCoConfig


config = CoCoConfig(survey_link='survey.link', database_url='database.url')

SQLALCHEMY_DATABASE_URL = CoCoConfig().database_url
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
