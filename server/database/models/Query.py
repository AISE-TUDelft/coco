from datetime import datetime

from pydantic import BaseModel
from database.models.Requests import GenerateRequest


class Query(BaseModel):
    """
    The Query class is a Pydantic BaseModel class that defines the structure of a query.
    The query class encapsulates the request and the response for a given request.
    """
    request             :GenerateRequest    # the request for code generation
    timestamps          :list[datetime]     # the timestamps at which the responses were shown to the user
    predictions         :list[str]          # the predictions made by the models
    prediction_times    :list[float]        # the time taken by the models to make the predictions
    serving_time        :float              # the time taken by the server to serve the request
    survey              :bool               # whether to ask the user for feedback
