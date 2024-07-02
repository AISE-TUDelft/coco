from fastapi_limiter.depends import RateLimiter
from fastapi import APIRouter, Depends

from models.Requests import GenerateRequest, VerifyRequest, SurveyRequest
from models.Responses import GenerateResponse, VerifyResponse, SurveyResponse
from models.CoCoConfig import CoCoConfig

router = APIRouter()
config = CoCoConfig(survey_link='survey.link', database_url='database.url')


# TODO: Try streaming to reduce latency
@router.post("/prediction/autocomplete", dependencies=[Depends(RateLimiter(times=1000, hours=1))])
async def autocomplete_v3(gen_req: GenerateRequest) -> GenerateResponse:
    return GenerateResponse(time=0.0, completions={})


@router.post("/prediction/verify", dependencies=[Depends(RateLimiter(times=1000, hours=1))])
async def verify_v3(verify_req: VerifyRequest) -> VerifyResponse:
    return VerifyResponse(success=True)


@router.post("/survey")
async def survey(survey_req: SurveyRequest) -> SurveyResponse:
    redirect_url = CoCoConfig().survey_link.replace("{user_id}", survey_req.user_id)
    return SurveyResponse(redirect_url=redirect_url)
