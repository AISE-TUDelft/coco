import datetime
import threading
import time
from typing import Union

import logging

import sqlalchemy.orm
from fastapi import FastAPI, APIRouter, Depends, Request
from starlette.responses import FileResponse
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
from models.Sessions import Session, SessionManager, UserSetting, delete_expired_sessions
# from completion import (chain as completion_chain)
from database import get_db
from database.crud import (get_user_by_token, get_all_plugin_versions, get_all_programming_languages,
                           get_all_trigger_types, get_all_db_models)
from models import (
    GenerateRequest, VerifyRequest, SurveyRequest, SessionRequest,
    GenerateResponse, VerifyResponse, SurveyResponse, SessionResponse, ErrorResponse,
    CoCoConfig
)

# logging config
logging.basicConfig(level=logging.INFO, filename='coco.log', filemode='a', format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
logger = logging.getLogger(__name__)


def cache_tables(app: FastAPI, server_db_session: sqlalchemy.orm.Session):
    """
    A function which attempts to cache some of the tables in memory for faster access.
    """
    try:
        # cache plugin versions
        plugin_versions = get_all_plugin_versions(server_db_session)
        app.plugin_versions = {}
        for plugin_versions in plugin_versions:
            app.plugin_versions[plugin_versions.version_name] = plugin_versions.version_id

        logger.log(logging.INFO, f'Cached plugin versions: {app.plugin_versions} with a total of {len(app.plugin_versions)} plugin versions.')

        # cache programming languages
        programming_languages = get_all_programming_languages(server_db_session)
        app.languages = {}
        for language in programming_languages:
            app.languages[language.language_name] = language.language_id

        logger.log(logging.INFO, f'Cached programming languages: {app.languages} with a total of {len(app.languages)} languages.')

        # cache trigger types
        trigger_types = get_all_trigger_types(server_db_session)
        app.trigger_types = {}
        for trigger_type in trigger_types:
            app.trigger_types[trigger_type.trigger_type_name] = trigger_type.trigger_type_id

        logger.log(logging.INFO, f'Cached trigger types: {app.trigger_types} with a total of {len(app.trigger_types)} trigger types.')

        # cache db models
        llms = get_all_db_models(server_db_session)
        app.llms = {}
        for model in llms:
            app.llms[model.model_name] = model.model_id

        logger.log(logging.INFO, f'Cached db models: {app.llms} with a total of {len(app.llms)} db models.')

    except Exception as e:
        logger.log(logging.ERROR, f'Error caching tables: {e}')
        raise e


@asynccontextmanager
async def lifespan(app: FastAPI):

    # fastAPI-Limiter stores user-based limits in a redis db
    # see https://pypi.org/project/fastapi-limiter/, but we use the
    # non-deprecated lifespans instead: https://fastapi.tiangolo.com/advanced/events/#alternative-events-deprecated
    # redis_connection = redis.from_url('redis://localhost', encoding='utf-8', decode_responses=True)
    # await FastAPILimiter.init(redis_connection)

    # I'm using global, instead of declaring these outside the function
    # scope, for clearer code
    app.config = config
    # app.chain = completion_chain
    app.server_db_session = get_db(app.config)

    # cache some of the tables in memory for faster access
    cache_tables(app, app.server_db_session)

    # keep track of how many times an IP address tries to create a session and fails
    app.failed_session_attempts = {}
    app.blacklisted_ips = set()

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

@router.post('/session/new')
async def new_session(session_req: SessionRequest, request: Request) -> Union[SessionResponse | ErrorResponse]:
    """
    Create a new session for the user. The session token is used to authenticate the user in subsequent requests.
    """
    # get the request IP address
    ip = request.client.host
    if ip in app.blacklisted_ips:
        logger.log(logging.ERROR, f'IP address {ip} is blacklisted -> session not created.')
        return ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.')
    logger.log(logging.INFO, f'User {session_req.user_id} requested a new session from version '
                             f'{session_req.version} of the plugin for {session_req.project_ide}.')
    user_id = session_req.user_id
    try:
        if existing_session := app.session_manager.get_session_id_by_user_token(user_id):
            logger.log(logging.ERROR, f'User {user_id} already has a session with session id {existing_session} -> session not created.')
            return SessionResponse(session_id=existing_session)
        user = get_user_by_token(app.server_db_session, user_id)
    except Exception as e:
        logger.log(logging.ERROR, f'Error getting user by token: {e}')
        return ErrorResponse(error='Error getting user by token -> session not created.')

    if user is None:
        # keep track of IP addresses and how many times they try to create a session and fail
        if ip in app.failed_session_attempts:
            app.failed_session_attempts[ip] += [datetime.datetime.now()]
        else:
            app.failed_session_attempts[ip] = [datetime.datetime.now()]
        if len(app.failed_session_attempts[ip]) >= app.config.max_failed_session_attempts:
            app.blacklisted_ips.add(ip)
            logger.log(logging.ERROR, f'IP address {ip} has been blacklisted -> session not created.')
            return ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.')
        logger.log(logging.ERROR, f'Invalid user token {session_req.user_id} - session not created.')
        return ErrorResponse(error='Invalid user token -> session not created.')
    else:
        db_session = get_db(app.config)
        session = Session(user_id=user_id, project_primary_language=session_req.project_language,
                          project_ide=session_req.project_ide, user_settings=session_req.user_settings,
                          db_session=db_session, project_coco_version=session_req.version)
        session_id = app.session_manager.add_session(session)
        logger.log(logging.INFO, f'New session created for user {session_req.user_id} with token {session_id}.')
        return SessionResponse(session_id=session_id)

@router.post('/session/end')
async def end_session(session_req: SessionRequest, request: Request) -> None | ErrorResponse:
    """ Endpoint to end a session """
    ip = request.client.host
    if ip in app.blacklisted_ips:
        logger.log(logging.ERROR, f'IP address {ip} is blacklisted -> session not ended.')
        return ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.')
    session = app.session_manager.get_session(session_req.session_id)
    if session is None:
        logger.log(logging.ERROR, f'Invalid session token {session_req.session_id} -> session not ended.')
        return ErrorResponse(error='Invalid session token -> session not ended.')
    app.session_manager.remove_session(session_req.session_id, app)
    logger.log(logging.INFO, f'Session {session_req.session_id} ended.')
    return None

@router.post('/complete')
async def autocomplete_v3(gen_req: GenerateRequest, request: Request) -> ErrorResponse | GenerateResponse:
    """ Endpoint to generate a dict of completions; {model_name: completion} """
    ip = request.client.host
    if ip in app.blacklisted_ips:
        logger.log(logging.ERROR, f'IP address {ip} is blacklisted -> no completions generated.')
        return ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.')
    session = app.session_manager.get_session(gen_req.session_id)
    if session is None:
        logger.log(logging.ERROR, f'Invalid session token {gen_req.session_id} -> no completions generated.')
        return ErrorResponse(error='Invalid session token -> no completions generated.')
    logger.log(logging.INFO, f'User {gen_req.session_id} requested completions with completion id {gen_req.request_id}.')
    if session is None:
        logger.log(logging.ERROR, f'Invalid session token {gen_req.session_id} -> no completions generated.')
        return ErrorResponse(error='Invalid session token -> no completions generated.')
    else:
        try:
            t = time.time()
            completions : dict[str, str] = app.chain.invoke(gen_req)
            t = time.time() - t # seconds (float)
            logger.log(logging.INFO, f'Completions generated for request with id {gen_req.request_id} in {t} seconds.')
            session.add_active_request(gen_req.request_id, completions, t)
            return GenerateResponse(time=t, completions=completions)
        except Exception as e:
            logger.log(logging.ERROR, f'Error generating completions: {e}')
            return ErrorResponse(error='Error generating completions.')

@router.post('/verify')
async def verify_v3(verify_req: VerifyRequest, request: Request) -> ErrorResponse | VerifyResponse:
    """ Endpoint to verify a completion """
    ip = request.client.host
    if ip in app.blacklisted_ips:
        logger.log(logging.ERROR, f'IP address {ip} is blacklisted -> no verification done.')
        return ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.')
    session = app.session_manager.get_session(verify_req.session_id)
    if session is None:
        logger.log(logging.ERROR, f'Invalid session token {verify_req.session_id} -> no verification done.')
        return ErrorResponse(error='Invalid session token -> no verification done.')
    session.update_active_request(verify_req.verify_token, verify_req) # update the active request with the verification
    return VerifyResponse(success=True)


@router.post('/survey')
async def survey(survey_req: SurveyRequest, request: Request) -> ErrorResponse | SurveyResponse:
    """ Endpoint to redirect to a survey """
    ip = request.client.host
    if ip in app.blacklisted_ips:
        logger.log(logging.ERROR, f'IP address {ip} is blacklisted -> no survey redirection.')
        return ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.')
    user_id = app.session_manager.get_session(survey_req.session_id).user_id
    redirect_url = app.config.survey_link.format(user_id=user_id)
    return SurveyResponse(redirect_url=redirect_url)

config = CoCoConfig()
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

