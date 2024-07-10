import datetime

from pydantic import BaseModel
from typing import List, Optional, Dict, Tuple

from models import GenerateRequest


class ModelCompletionDetails(BaseModel):
    completion: str
    shown_at: List[datetime.datetime]
    accepted: bool = False


class ActiveRequest(BaseModel):
    request: GenerateRequest
    completions: Dict[str, ModelCompletionDetails]
    time_taken: int
    ground_truth: List[Tuple[datetime.datetime, str]] = []
