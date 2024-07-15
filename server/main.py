import datetime
import json
import threading
import time
from typing import Union

import os
import logging

import sqlalchemy.orm
from fastapi import FastAPI, APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from starlette.responses import FileResponse
from contextlib import asynccontextmanager
from sqlalchemy import create_engine

from models.Requests import SessionEndRequest
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

import pickle


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


def request_in_limit(app: FastAPI, session: Session):
    """
    A function which checks if the user has exceeded the request limit.
    """
    time_diff = (datetime.datetime.now() - session.get_session_since()).total_seconds()
    if time_diff < 300: # 5 minutes
        return True
    time_diff = time_diff / 3600 # convert to hours
    if ((session.get_user_request_count() + 1) / time_diff) > app.config.max_request_rate:
        logger.log(logging.ERROR, f'User {session.user_id} has exceeded the request limit of {app.config.max_user_requests} -> no completions generated.')
        return False
    return True


@asynccontextmanager
async def lifespan(app: FastAPI):

    # fastAPI-Limiter stores user-based limits in a redis db
    # see https://pypi.org/project/fastapi-limiter/, but we use the
    # non-deprecated lifespans instead: https://fastapi.tiangolo.com/advanced/events/#alternative-events-deprecated
    # redis_connection = redis.from_url('redis://localhost', encoding='utf-8', decode_responses=True)
    # await FastAPILimiter.init(redis_connection)

    app.config = config
    # app.chain = completion_chain
    app.server_db_session = get_db(app.config)

    # check whether a pickle file exists for some of the values
    # if so, load them into the app object
    # check whether a cache/cache.pkl file exists

    try:
        with open("cache/cache.pkl", "rb") as f:
            state_dict = pickle.load(f)
            app.failed_session_attempts = state_dict["failed_session_attempts"]
            app.blacklisted_ips = state_dict["blacklisted_ips"]
    except (FileNotFoundError, KeyError) as e:
        # keep track of how many times an IP address tries to create a session and fails
        app.failed_session_attempts = {}
        app.blacklisted_ips = set()

    # cache some of the tables in memory for faster access
    cache_tables(app, app.server_db_session)
    app.session_manager = SessionManager(app.config.session_length)
    stop_event = threading.Event()
    app.cleaning_thread = threading.Thread(target=delete_expired_sessions, args=(app.session_manager, stop_event), daemon=True)
    app.cleaning_thread.start()

    yield

    # save the cache to a pickle file
    try:
        with open("cache/cache.pkl", "wb") as f:
            pickle.dump({"failed_session_attempts": app.failed_session_attempts, "blacklisted_ips": app.blacklisted_ips}, f)
    except FileNotFoundError as e:
        os.makedirs("cache")
        with open("cache/cache.pkl", "wb") as f:
            pickle.dump({"failed_session_attempts": app.failed_session_attempts, "blacklisted_ips": app.blacklisted_ips}, f)

    # close the server db session
    app.server_db_session.close()

    # go through the session manager and close / end all the sessions
    # this ensures that the sessions are properly ended and the resources are freed
    # we don't want any dangling sessions / memory leaks
    sessions = list(app.session_manager.get_sessions().keys())
    for session_id in sessions:
        app.session_manager.remove_session(session_id, app, logger)

    # send a signal to kill the cleaning thread
    stop_event.set()
    app.cleaning_thread.join()

    # TODO: potential generation model cleanup here
    pass

# --------------------- Normal API Endpoints ---------------------

router = APIRouter(prefix='/api/v3')

# TODO: Try streaming to reduce latency
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
            app.failed_session_attempts[ip].append(datetime.datetime.now())
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
async def end_session(session_end_req: SessionEndRequest, request: Request) -> None | ErrorResponse:
    """ Endpoint to end a session """
    ip = request.client.host
    if ip in app.blacklisted_ips:
        logger.log(logging.ERROR, f'IP address {ip} is blacklisted -> session not ended.')
        return ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.')
    session = app.session_manager.get_session(session_end_req.session_token)
    if session is None:
        logger.log(logging.ERROR, f'Invalid session token {session_end_req.session_token} -> No session to end.')
        return ErrorResponse(error='Invalid session token -> No session to end.')
    app.session_manager.remove_session(session_end_req.session_token, app, logger)
    logger.log(logging.INFO, f'Session {session_end_req.session_token} ended.')
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
            if not request_in_limit(app, session):
                return ErrorResponse(error='User has exceeded the request limit -> no completions generated.')
            t = time.time()
            completions : dict[str, str] = app.chain.invoke(gen_req)
            t = time.time() - t # seconds (float)
            logger.log(logging.INFO, f'Completions generated for request with id {gen_req.request_id} in {t} seconds.')
            session.add_active_request(gen_req.request_id, completions, t)
            session.increment_user_request_count()
            return GenerateResponse(time=t, completions=completions)
        except Exception as e:
            logger.log(logging.ERROR, f'Error generating completions: {e}')
            return ErrorResponse(error='Error generating completions.')

@router.post('/verify')
async def verify_v3(verify_req: VerifyRequest, request: Request) -> ErrorResponse | VerifyResponse:
    """
    Endpoint to verify a completion
    Note -> verification of the completion can be still carried out even if the request limit has been exceeded.
    """
    ip = request.client.host
    if ip in app.blacklisted_ips:
        logger.log(logging.ERROR, f'IP address {ip} is blacklisted -> no verification done.')
        return ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.')
    session = app.session_manager.get_session(verify_req.session_id)
    if session is None:
        logger.log(logging.ERROR, f'Invalid session token {verify_req.session_id} -> no verification done.')
        return ErrorResponse(error='Invalid session token -> no verification done.')
    # TODO: update this implementation to be more robust after the completion of the MVPs for the server
    # Details -> the current implementation will fail given that a verify request is sent for a session that has
    # ended or requests that have already been stored to the DB. It might be the case that we would want to do a
    # more longitudinal study of the completions generated and verified and thus we would want to store all the
    # completions generated and verified in the DB -> This would necessitate a change in the current implementation
    session.update_active_request(verify_req.verify_token, verify_req) # update the active request with the verification
    return VerifyResponse(success=True)


@router.post('/survey')
async def survey(survey_req: SurveyRequest, request: Request) -> ErrorResponse | SurveyResponse:
    """
    Endpoint to redirect to a survey
    Note -> survey redirection can be still carried out even if the request limit has been exceeded.
    """
    ip = request.client.host
    if ip in app.blacklisted_ips:
        logger.log(logging.ERROR, f'IP address {ip} is blacklisted -> no survey redirection.')
        return ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.')
    user_id = app.session_manager.get_session(survey_req.session_id).get_user_id()
    redirect_url = app.config.survey_link.format(user_id=user_id)
    return SurveyResponse(redirect_url=redirect_url)

# --------------------- WebSocket Endpoints ---------------------
class WebSocketManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(message)

manager = WebSocketManager()

@router.websocket("/ws/session/new")
async def websocket_new_session(websocket: WebSocket):
    await manager.connect(websocket, "new_session")
    try:
        while True:
            data = await websocket.receive_text()
            session_req = SessionRequest(**json.loads(data))
            response = await new_session(session_req)
            await manager.send_message("new_session", json.dumps(response.model_dump()))
    except WebSocketDisconnect:
        manager.disconnect("new_session")

@router.websocket("/ws/session/end")
async def websocket_end_session(websocket: WebSocket):
    await manager.connect(websocket, "end_session")
    try:
        while True:
            data = await websocket.receive_text()
            session_req = SessionRequest(**json.loads(data))
            response = await end_session(session_req)
            await manager.send_message("end_session", json.dumps(response.model_dump() if response else {}))
    except WebSocketDisconnect:
        manager.disconnect("end_session")

@router.websocket("/ws/complete")
async def websocket_autocomplete(websocket: WebSocket):
    await manager.connect(websocket, "autocomplete")
    try:
        while True:
            data = await websocket.receive_text()
            gen_req = GenerateRequest(**json.loads(data))
            response = await autocomplete_v3(gen_req)
            await manager.send_message("autocomplete", json.dumps(response.model_dump()))
    except WebSocketDisconnect:
        manager.disconnect("autocomplete")

@router.websocket("/ws/verify")
async def websocket_verify(websocket: WebSocket):
    await manager.connect(websocket, "verify")
    try:
        while True:
            data = await websocket.receive_text()
            verify_req = VerifyRequest(**json.loads(data))
            response = await verify_v3(verify_req)
            await manager.send_message("verify", json.dumps(response.model_dump()))
    except WebSocketDisconnect:
        manager.disconnect("verify")

@router.websocket("/ws/survey")
async def websocket_survey(websocket: WebSocket):
    await manager.connect(websocket, "survey")
    try:
        while True:
            data = await websocket.receive_text()
            survey_req = SurveyRequest(**json.loads(data))
            response = await survey(survey_req)
            await manager.send_message("survey", json.dumps(response.model_dump()))
    except WebSocketDisconnect:
        manager.disconnect("survey")

# --------------------- Configuration Logic ---------------------

config = CoCoConfig()
app = FastAPI(
    title       = 'CoCo API',
    description = 'RESTful API that provides code completion services to the CoCo IDE plugin.',
    version     = '0.0.1',
    lifespan    = lifespan,
)

app.include_router(router)

# --------------------- Static File Serving ---------------------

@app.get('/')
@app.get('/index.html')
async def root():
    return FileResponse('./static/index.html')

