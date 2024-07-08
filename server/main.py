import threading
import time
from typing import Union

import sqlalchemy.orm
from fastapi import FastAPI, APIRouter, Depends
from starlette.responses import FileResponse
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from models.Sessions import Session, SessionManager, UserSetting, delete_expired_sessions
from completion import (chain as completion_chain)
from database import get_db
from database.crud import get_user_by_token
from models import (
    GenerateRequest, VerifyRequest, SurveyRequest, SessionRequest,
    GenerateResponse, VerifyResponse, SurveyResponse, SessionResponse, ErrorResponse,
    CoCoConfig
)


@asynccontextmanager
async def lifespan(fastapi: FastAPI):

    # fastAPI-Limiter stores user-based limits in a redis db
    # see https://pypi.org/project/fastapi-limiter/, but we use the
    # non-deprecated lifespans instead: https://fastapi.tiangolo.com/advanced/events/#alternative-events-deprecated
    # redis_connection = redis.from_url('redis://localhost', encoding='utf-8', decode_responses=True)
    # await FastAPILimiter.init(redis_connection)

    # I'm using global, instead of declaring these outside the function
    # scope, for clearer code
    app.config = CoCoConfig()
    app.chain = completion_chain
    app.server_db_session = get_db(app.config)
    app.session_manager = SessionManager(app.config.session_length)
    app.cleaning_thread = threading.Thread(target=delete_expired_sessions, args=(app.session_manager,), daemon=True)
    app.cleaning_thread.start()

    yield

    # TODO: potential generation model cleanup here
    pass

router = APIRouter(prefix='/api/v3')

# TODO: Try streaming to reduce latency
# TODO: Rate limiting 
# TODO: Can squeeze out a little more performance with https://fastapi.tiangolo.com/advanced/custom-response/#use-orjsonresponse
# TODO: Authentication & Session management (also with db?)

@router.post('/session/new')
async def new_session(session_req: SessionRequest) -> Union[SessionResponse | ErrorResponse]:
    user_id = session_req.user_id
    user = get_user_by_token(app.server_db_session, user_id)
    if user is None:
        return ErrorResponse(error='Invalid user token -> session not created.')
    else:
        db_session = get_db(app.config)
        session = Session(user_id=user_id, project_primary_language=session_req.project_language,
                          project_ide=session_req.project_ide, user_settings=session_req.user_settings,
                          db_session=db_session)
        session_token = app.session_manager.add_session(session)
        return SessionResponse(session_token=session_token)


@router.post('/complete')
async def autocomplete_v3(gen_req: GenerateRequest) -> GenerateResponse:
    ''' Endpoint to generate a dict of completions; {model_name: completion} '''

    t = time.time()
    completions : dict[str, str] = app.chain.invoke(gen_req)
    t = time.time() - t # seconds (float)

    return GenerateResponse(time=t, completions=completions)

@router.post('/verify')
async def verify_v3(verify_req: VerifyRequest) -> VerifyResponse:
    return VerifyResponse(success=True)


@router.post('/survey')
async def survey(survey_req: SurveyRequest) -> SurveyResponse:
    redirect_url = app.config.survey_link.format(user_id=survey_req.user_id)
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

