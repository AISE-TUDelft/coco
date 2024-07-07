import time

from fastapi import FastAPI, APIRouter
from starlette.responses import FileResponse
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .database import get_db
from .models import (
    GenerateRequest, VerifyRequest, SurveyRequest, 
    GenerateResponse, VerifyResponse, SurveyResponse,
    CoCoConfig 
)

@asynccontextmanager
async def lifespan(app: FastAPI):

    # fastAPI-Limiter stores user-based limits in a redis db
    # see https://pypi.org/project/fastapi-limiter/, but we use the 
    # non-deprecated lifespans instead: https://fastapi.tiangolo.com/advanced/events/#alternative-events-deprecated
    # redis_connection = redis.from_url('redis://localhost', encoding='utf-8', decode_responses=True)
    # await FastAPILimiter.init(redis_connection)

    # I'm using global, instead of declaring these outside the function
    # scope, for clearer code
    global config
    config = CoCoConfig()

    from .completion import chain as completion_chain 
    global chain
    chain = completion_chain

    # TODO: per-user session management
    global session
    session = get_db(config)

    yield

    # TODO: potential generation model cleanup here
    pass 

router = APIRouter(prefix='/api/v3')

# TODO: Try streaming to reduce latency
# TODO: Rate limiting 
# TODO: Can squeeze out a little more performance with https://fastapi.tiangolo.com/advanced/custom-response/#use-orjsonresponse
# TODO: Authentication & Session management (also with db?)
@router.post('/complete')
async def autocomplete_v3(gen_req: GenerateRequest) -> GenerateResponse:
    ''' Endpoint to generate a dict of completions; {model_name: completion} '''

    t = time.time()
    completions : dict[str, str] = chain.invoke(gen_req)
    t = time.time() - t # seconds (float)

    return GenerateResponse(time=t, completions=completions)

@router.post('/verify')
async def verify_v3(verify_req: VerifyRequest) -> VerifyResponse:
    return VerifyResponse(success=True)


@router.post('/survey')
async def survey(survey_req: SurveyRequest) -> SurveyResponse:
    redirect_url = config.survey_link.format(user_id=survey_req.user_id)
    return SurveyResponse(redirect_url=redirect_url)

app = FastAPI(
    title       = 'CoCo API',
    description = 'RESTful API that provides code completion services to the CoCo IDE plugin.',
    version     = '0.0.1',
    lifespan    = lifespan,
)
app.include_router(router)
@app.get('/')
@app.get('/index.html')
async def root():
    return FileResponse('./static/index.html')

