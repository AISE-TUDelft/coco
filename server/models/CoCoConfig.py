from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class CoCoConfig(BaseSettings):
    """
    A Pydantic BaseModel defining the structure of the configuration file for CoCo.
    This configuration file is meant to be used to configure the CoCo server.
    """
    survey_link: str  # the link to the survey
    # # TODO: change this to be always required - done this way as the database is not yet set up
    database_url: Optional[str]  # the url to the database
    test_database_url: Optional[str]  # the url to the test database
    #
    # class Config:
    #     env_file = "../.env"
    model_config = SettingsConfigDict(env_file="../.env")
