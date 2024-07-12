import datetime

from pydantic import BaseModel
from typing import List, Optional, Dict, Tuple

from models import GenerateRequest


class ModelCompletionDetails(BaseModel):
    completion: str
    shown_at: List[datetime.datetime]
    accepted: bool = False

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)


class ActiveRequest(BaseModel):
    request: GenerateRequest
    completions: Dict[str, ModelCompletionDetails]
    time_taken: int
    ground_truth: List[Tuple[datetime.datetime, str]] = []
