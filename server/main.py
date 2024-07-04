import asyncio, time

from fastapi import FastAPI, APIRouter
from starlette.responses import FileResponse
from contextlib import asynccontextmanager

from .models.Requests import GenerateRequest, VerifyRequest, SurveyRequest
from .models.Responses import GenerateResponse, VerifyResponse, SurveyResponse
from .models.CoCoConfig import CoCoConfig


models = {} 
@asynccontextmanager
async def lifespan(app: FastAPI):

    # fastAPI-Limiter stores user-based limits in a redis db
    # see https://pypi.org/project/fastapi-limiter/, but we use the 
    # non-deprecated lifespans instead: https://fastapi.tiangolo.com/advanced/events/#alternative-events-deprecated
    # redis_connection = redis.from_url('redis://localhost', encoding='utf-8', decode_responses=True)
    # await FastAPILimiter.init(redis_connection)

    # TODO: set up the generation models as a branched langchain
    # see https://python.langchain.com/v0.1/docs/expression_language/cookbook/multiple_chains/#branching-and-merging
    from .completion.models import Models
    global models
    models = Models

    yield

    # TODO: potential generation model cleanup here
    pass 

router = APIRouter(prefix='/api/v3')
config = CoCoConfig(survey_link='survey.link/{user_id}', database_url='database.url', test_database_url='test.database.url')

# TODO: Try streaming to reduce latency
# TODO: Rate limiting 
# TODO: Can squeeze out a little more performance with https://fastapi.tiangolo.com/advanced/custom-response/#use-orjsonresponse
@router.post('/complete')
async def autocomplete_v3(gen_req: GenerateRequest) -> GenerateResponse:
    ''' Endpoint to generate a dict of completions; {model_name: completion} '''
    t = time.time()

    # TODO: parallel processing: this section needs a whole rewrite for async
    # completions = await asyncio.gather(model(inputs) for model in models)
    # NOTE: could write your own langchain PromptTemplate that expects a GenerateRequest
    # but let's save some time: https://api.python.langchain.com/en/latest/prompts/langchain_core.prompts.prompt.PromptTemplate.html 
    inputs = {'prefix': gen_req.prefix, 'suffix': gen_req.suffix}
    completions = [model(inputs) for model in models]
    completions = dict(zip(models.values(), [completion.text for completion in completions]))

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


