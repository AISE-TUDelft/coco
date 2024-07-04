from pydantic import BaseModel
from typing import Union

from .Types import TriggerType, LanguageType, IDEType

class GenerateRequest(BaseModel):
    """
    The GenerateRequest class is a Pydantic BaseModel class that defines the structure of a request for code generation.
    This request is meant to be used along with the /generate endpoint.
    """
    user_id     :str            # uuid
    request_id  :str            # uuid
    prefix      :str            # the context before the point of generation
    suffix      :str            # the context after the point of generation
    trigger     :TriggerType    # see TriggerType in Types.py
    language    :LanguageType   # see LanguageType in Types.py
    ide         :IDEType        # see IDEType in Types.py
    version     :str            # the version of the extension
    store       :bool           # whether to store the request in the database


class VerifyRequest(BaseModel):
    """
    The VerifyRequest class is a Pydantic BaseModel class that defines the structure of the verification request.
    This request is meant to be used along with the /verify endpoint.
    It is used to gain input about the chosen completion (if any) as well as the ground truth of the completion.
    """
    verify_token: str               # the uuid of the request to be verified
    chosen_model: Union[str, None]  # the model chosen by the user
    ground_truth: str               # the ground truth of the completion


class SurveyRequest(BaseModel):
    """
    The SurveyRequest class is a Pydantic BaseModel class that defines the structure of the survey request.
    This request is meant to be used along with the /survey endpoint.
    It is used to gain input about the user's experience with the extension.
    """
    user_id: str  # uuid
