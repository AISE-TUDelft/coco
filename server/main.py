import asyncio, time

from fastapi import FastAPI, APIRouter
from starlette.responses import FileResponse
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .models.Requests import GenerateRequest, VerifyRequest, SurveyRequest
from .models.Responses import GenerateResponse, VerifyResponse, SurveyResponse
from .models.CoCoConfig import CoCoConfig

@asynccontextmanager
async def lifespan(app: FastAPI):

    # fastAPI-Limiter stores user-based limits in a redis db
    # see https://pypi.org/project/fastapi-limiter/, but we use the 
    # non-deprecated lifespans instead: https://fastapi.tiangolo.com/advanced/events/#alternative-events-deprecated
    # redis_connection = redis.from_url('redis://localhost', encoding='utf-8', decode_responses=True)
    # await FastAPILimiter.init(redis_connection)

    # database = create_engine(config.database_url)
    # global session # I think I'm using this keyword right but im not sure
    # session = Session(database)

    # TODO: set up the generation models as a branched langchain
    # see https://python.langchain.com/v0.1/docs/expression_language/cookbook/multiple_chains/#branching-and-merging
    from .completion import chain as completion_chain 
    global chain
    chain = completion_chain

    yield

    # TODO: potential generation model cleanup here
    pass 

config = CoCoConfig(
    survey_link         = 'survey.link/{user_id}', 
    database_url        = 'database.url', 
    test_database_url   = 'test.database.url'
)
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
