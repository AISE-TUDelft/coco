import datetime

from pydantic import BaseModel
from typing import Union, Dict

from .Types import TriggerType, LanguageType, IDEType


class GenerateRequest(BaseModel):
    """
    The GenerateRequest class is a Pydantic BaseModel class that defines the structure of a request for code generation.
    This request is meant to be used along with the /generate endpoint.
    """
    session_id: str  # uuid
    request_id: str  # uuid
    prefix: str  # the context before the point of generation
    suffix: str  # the context after the point of generation
    trigger: TriggerType  # see TriggerType in Types.py
    language: LanguageType  # see LanguageType in Types.py

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "123aaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                    "request_id": "123bbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                    "prefix": "import numpy as np\n\ndef main(): \n    items = [1,2,3]\n\n    # convert items to numpy array \n    arr = ",
                    "suffix": "\n\n    # get the data type\n    print(arr.dtype)",
                    "trigger": "auto",
                    "language": "python"
                }
            ]
        }
    }


class VerifyRequest(BaseModel):
    """
    The VerifyRequest class is a Pydantic BaseModel class that defines the structure of the verification request.
    This request is meant to be used along with the /verify endpoint.
    It is used to gain input about the chosen completion (if any) as well as the ground truth of the completion.
    """
    verify_token: str  # the uuid of the request to be verified
    chosen_model: Union[str, None]  # the model chosen by the user
    shown_at: Union[dict[str, list[datetime.datetime]], None]
    # the timestamps at which the completions were shown to the user
    ground_truth: Union[str, None]  # the ground truth of the completion


class SessionRequest(BaseModel):
    """
    The SessionRequest class is a Pydantic BaseModel class that defines the structure of the session request.
    This request is meant to be used along with the /session/new endpoint.
    It is used to gain a session token for the user based on the user's personal token
    """
    user_id: str # uuid
    project_language: Union[LanguageType, None]  # see LanguageType in Types.py -> this would be the most used language in the project
    project_ide: Union[IDEType, None]  # see IDEType in Types.py -> this would be the most used IDE in the project
    user_settings: Union[Dict, None]  # see UserSettings in Types.py -> this would be the user's settings
    version: str  # the version of the extension
    ide: IDEType  # see IDEType in Types.py



class SurveyRequest(BaseModel):
    """
    The SurveyRequest class is a Pydantic BaseModel class that defines the structure of the survey request.
    This request is meant to be used along with the /survey endpoint.
    It is used to gain input about the user's experience with the extension.
    """
    session_id: str  # uuid

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "session_id": "123aaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
                }
            ]
        }
    }