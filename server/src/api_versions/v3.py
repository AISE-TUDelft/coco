from fastapi import APIRouter

from models.Requests import GenerateRequest, VerifyRequest
from models.Responses import GenerateResponse
from models.Query import Query


router = APIRouter()


@router.get("/generate")
async def generate(gen_req: GenerateRequest) -> GenerateResponse:
    return GenerateResponse(time=0.0, completions={})

