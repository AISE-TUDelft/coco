from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class CoCoConfig(BaseSettings):
    '''
    Defines the configuration file for CoCo, immutable.
    '''
    model_config = SettingsConfigDict(env_file='.env')

    survey_link: str = Field(alias='SURVEY_LINK', frozen=True)
    database_url: str = Field(alias='DATABASE_URL', frozen=True)
    test_database_url: str = Field(alias='TEST_DATABASE_URL', frozen=True)
