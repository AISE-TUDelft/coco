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
    session_length: int = Field(alias='SESSION_LENGTH', frozen=True)
    max_failed_session_attempts: int = Field(alias='MAX_FAILED_SESSION_ATTEMPTS', frozen=True)
    server_version_id: int = Field(alias='SERVER_VERSION_ID', frozen=True)
    max_request_rate: int = Field(alias='MAX_REQUEST_RATE', frozen=True) # maximum amount of requests that are allowed per hour per user -> 1000 would indicate 1000 requests per hour