from typing import Optional

from pydantic_settings import BaseSettings


class CoCoConfig(BaseSettings):
    """
    The CoCoConfig class is a Pydantic BaseModel class that defines the structure of the configuration file for CoCo.
    This configuration file is meant to be used to configure the CoCo server.
    """
    survey_link: str  # the link to the survey

    # TODO: change this to be always required - done this way as the database is not yet set up
    database_url: Optional[str]  # the url to the database

    class Config:
        env_file = "coco.env"
