from pydantic import BaseModel


class GenerateResponse(BaseModel):
    """
    The GenerateResponse class is a Pydantic BaseModel class that defines the structure of a response for
        the generation process.
    This response is meant to be used along with the /generate endpoint as a response to a GenerateRequest
        (models/Requests.py).
    """
    time        :float          # the time taken by the server to generate the completions
    completions :dict[str, str] # the completions generated by the models


class VerifyResponse(BaseModel):
    """
    The VerifyResponse class is a Pydantic BaseModel class that defines the structure of a response for
        the verification process.
    This response is meant to be used along with the /verify endpoint as a response to a VerifyRequest.
    """
    success: bool  # whether the verification was successful


class SurveyResponse(BaseModel):
    """
    The SurveyResponse class is a Pydantic BaseModel class that defines the structure of a response for
        the survey process.
    This response is meant to be used along with the /survey endpoint as a response to a SurveyRequest.
    """
    redirect_url: str  # the url to redirect the user to
