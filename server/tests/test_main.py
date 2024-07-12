import datetime
from unittest.mock import MagicMock, patch, AsyncMock

import os
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from fastapi import FastAPI

from fastapi.testclient import TestClient
from starlette.requests import Request

from models import (
    GenerateRequest, SurveyRequest, SurveyResponse,
    GenerateResponse, Session, SessionRequest, ErrorResponse, VerifyRequest
)

from fastapi.responses import FileResponse

from models.Requests import SessionEndRequest

global config

class TestCoCoAPI:

    @pytest.fixture(scope='function')
    def client(self):
        """ Run the FastAPI server with its lifespan context """
        load_dotenv()
        from main import app, config as _config
        global config
        config = _config

        with TestClient(app) as client:
            yield client

        # check whether a cache folder exists and delete it even if it's not empty
        if os.path.exists('cache'):
            os.system('rm -rf cache')

    # testing the helper functions

    @patch('main.get_all_plugin_versions')
    @patch('main.get_all_programming_languages')
    @patch('main.get_all_trigger_types')
    @patch('main.get_all_db_models')
    def test_cache_tables(self, mock_get_all_db_models, mock_get_all_trigger_types, mock_get_all_programming_languages,
                          mock_get_all_plugin_versions, client):
        # setup
        print("working directory: ", os.getcwd())

        from main import cache_tables

        # Arange
        mock_plugin_versions = [MagicMock(version_name='1.0.0a', version_id=1), MagicMock(version_name='1.0.0b', version_id=2)]
        mock_programming_languages = [MagicMock(language_name='Python', language_id=1),
                                      MagicMock(language_name='JavaScript', language_id=2)]
        mock_trigger_types = [MagicMock(trigger_type_name='man', trigger_type_id=1),
                              MagicMock(trigger_type_name='auto', trigger_type_id=2)]
        mock_db_models = [MagicMock(model_name='model_1', model_id=1), MagicMock(model_name='model_2', model_id=2)]

        mock_get_all_plugin_versions.return_value = mock_plugin_versions
        mock_get_all_programming_languages.return_value = mock_programming_languages
        mock_get_all_trigger_types.return_value = mock_trigger_types
        mock_get_all_db_models.return_value = mock_db_models

        mock_app = MagicMock()
        mock_server_db_session = MagicMock()

        # Act
        cache_tables(mock_app, mock_server_db_session)

        # Assert
        assert mock_app.plugin_versions == {'1.0.0a': 1, '1.0.0b': 2}
        assert mock_app.languages == {'Python': 1, 'JavaScript': 2}
        assert mock_app.trigger_types == {'man': 1, 'auto': 2}
        assert mock_app.llms == {'model_1': 1, 'model_2': 2}

    def test_request_in_limit_in_limit(self, client):
        from main import request_in_limit

        # Arrange
        mock_session = MagicMock(spec=Session)
        mock_session.get_session_since.return_value = datetime.datetime.now() - datetime.timedelta(hours=1)
        mock_session.get_user_request_count.return_value = 200
        mock_app = MagicMock(spec=FastAPI)
        mock_app.config = MagicMock()
        mock_app.config.max_request_rate = 1000

        # Act / Assert
        assert request_in_limit(mock_app, mock_session) == True

    def test_request_in_limit_out_of_limit(self, client):
        from main import request_in_limit

        # Arrange
        mock_session = MagicMock(spec=Session)
        mock_session.user_id = "test_user_id"
        mock_session.get_session_since.return_value = datetime.datetime.now() - datetime.timedelta(hours=1)
        mock_session.get_user_request_count.return_value = 1200
        mock_app = MagicMock(spec=FastAPI)
        mock_app.config = MagicMock()
        mock_app.config.max_request_rate = 1000

        # Act / Assert
        assert request_in_limit(mock_app, mock_session) == False


    def test_request_in_limit_new_session(self, client):
        from main import request_in_limit

        # Arrange
        mock_session = MagicMock(spec=Session)
        mock_session.get_session_since.return_value = datetime.datetime.now() - datetime.timedelta(minutes=1)
        mock_session.get_user_request_count.return_value = 0
        mock_app = MagicMock(spec=FastAPI)
        mock_app.config = MagicMock()
        mock_app.config.max_request_rate = 1000

        # Act / Assert
        assert request_in_limit(mock_app, mock_session) == True

    def test_request_in_limit_on_limit(self, client):
        from main import request_in_limit

        # Arrange
        mock_session = MagicMock(spec=Session)
        mock_session.get_session_since.return_value = datetime.datetime.now() - datetime.timedelta(hours=1)
        mock_session.get_user_request_count.return_value = 999
        mock_app = MagicMock(spec=FastAPI)
        mock_app.config = MagicMock()
        mock_app.config.max_request_rate = 1000

        # Act / Assert
        assert request_in_limit(mock_app, mock_session) == True

    def test_homepage(self, client):
        """ Test whether the homepage is accessible """
        # go one level higher in the directory to have access to the static folder
        os.chdir('..')  # I literally lost brain cells trying to figure this out

        response = client.get("/")
        response2 = client.get("/index.html")

        assert response.status_code == 200
        assert response2.status_code == 200
        assert response.headers['content-type'] == 'text/html; charset=utf-8'
        assert response2.headers['content-type'] == 'text/html; charset=utf-8'

    def test_blacklisting_with_invalid_attempts(self, client):
        # Arrange
        test_ip = "192.168.1.1"
        session_req_invalid_token = SessionRequest(user_id="invalid_token", version="1.0.0", project_ide="VSCode",
                                     project_language="python", user_settings={})
        session_req_invalid_user = SessionRequest(user_id=str(uuid4()), version="1.0.0", project_ide="VSCode",
                                        project_language="python", user_settings={})
        global config
        maximum_tries = config.max_failed_session_attempts

        # Act
        # attempt 1 wih invalid token
        response = client.post("/api/v3/session/new", json=session_req_invalid_token.model_dump(), headers={"X-Forwarded-For": test_ip})
        assert response.status_code == 200
        assert response.json() == ErrorResponse(error='Error getting user by token -> session not created.').model_dump()

        # attempt 2 with invalid user
        response = client.post("/api/v3/session/new", json=session_req_invalid_user.model_dump(), headers={"X-Forwarded-For": test_ip})
        assert response.status_code == 200
        assert response.json() == ErrorResponse(error='Invalid user token -> session not created.').model_dump()

        for i in range(maximum_tries - 1): # the reason 1 and not 2 is because invalid tokens are not counted as failed attempts
            response = client.post("/api/v3/session/new", json=session_req_invalid_user.model_dump(), headers={"X-Forwarded-For": test_ip})
            assert response.status_code == 200

        # attempt after blacklisting
        response_after_blacklist = client.post("/api/v3/session/new", json=session_req_invalid_user.model_dump(), headers={"X-Forwarded-For": test_ip})

        # Assert
        assert response.json() == ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.').model_dump()
        assert response_after_blacklist.json() == ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.').model_dump()


    @patch('main.get_user_by_token')
    def test_getting_session_for_valid_user_and_check_not_new_session_created_upon_repeated_request(self, mocked_get_user_by_token, client):
        # Arrange
        mocked_user = MagicMock()
        mocked_get_user_by_token.return_value = mocked_user

        patch('main.app.session_manager.remove_session')

        session_req = SessionRequest(user_id=str(uuid4()), version="1.0.0", project_ide="VSCode",
                                                  project_language="python", user_settings={})

        # Act
        response = client.post("/api/v3/session/new", json=session_req.model_dump())

        # Assert
        assert response.status_code == 200
        assert response.json()["session_id"] is not None

        session_id = response.json()["session_id"]

        response2 = client.post("/api/v3/session/new", json=session_req.model_dump())

        assert response2.status_code == 200
        assert response2.json()["session_id"] == session_id




    #
    # def test_verification(self, client):
    #         raise NotImplementedError('TODO: test the verification endpoint')
    #
    # def test_survey(self, client):
    #     """
    #     Check we can send a SurveyRequest and parse
    #     the response as a SurveyResponse.
    #     """
    #     # might as well test with the API examples right
    #     example_req = SurveyRequest.model_config['json_schema_extra']['examples'][0]
    #     user_id = example_req['user_id']
    #     survey_link = config.survey_link.format(user_id=user_id)
    #
    #     response = client.post('api/v3/survey',
    #                         json=SurveyRequest(user_id=user_id).model_dump())
    #
    #     assert response.status_code == 200
    #     response = SurveyResponse(**response.json())
    #     assert response.redirect_url == survey_link
    #
    #
    # def test_generation(self):
    #     """
    #     Issue a single completion request, end-to-end
    #     testing the endpoints.
    #     """
    #     # FastAPI context managers require you to wrap it before you tap it
    #     # in a test https://fastapi.tiangolo.com/advanced/testing-events/
    #     # TODO: refactor this to a setup/teardown fixture somehow.
    #     with TestClient(app) as client:
    #
    #         gen_req = GenerateRequest.model_config['json_schema_extra']['examples'][0]
    #         json = GenerateRequest(**gen_req | {'store': False}).model_dump()
    #         response = client.post('api/v3/complete', json=json)
    #
    #         assert response.status_code == 200
    #         assert len(response.json()['completions']) > 0
    #
    #         # TODO: let's also assert that these things are in fact stored
    #         json = GenerateRequest(**gen_req | {'store': True})
    #         raise NotImplementedError('TODO: test that the request is stored')
    #
    # def test_generation_is_not_stored(self):
    #     """
    #     Issue a single completion request, end-to-end
    #     testing the endpoints, but with the `store` flag set to False
    #     """
    #     raise NotImplementedError('TODO: test that the request is not stored')
    #
    #
    # def test_batch_generation(self):
    #     """
    #     Issue a bunch of requests, making sure the time taken
    #     is less than the sum of each individual request
    #     (i.e. that batching actually works)
    #
    #     TODO: We need florimondmanca/asgi-lifespan to correctly set up the
    #     lifespan, according to  https://fastapi.tiangolo.com/advanced/async-tests/
    #     """
    #     raise NotImplementedError('TODO: test that the time taken is less than the sum of each individual request')
    #

# TODO: Testing generation API likely needs a separate file 
# with more exhaustive tests for measuring inference speed 
# and ensuring non-regression in subsequent updates.


# NOTE: leaving two functions here in case it's useful for future testing
# pre, suf = '''
# import numpy as np

# def main(): 
#     items = [1,2,3]

#     # convert items to numpy array 
#     arr = ｜

#     # get the data type
#     print(arr.dtype)

# '''.strip().split('｜')

# # helper for debugging what is generated exactly in FIM
# grey = '\033[90m{}\033[0m'
# print_fim = lambda gen: print(''.join([
#     grey.format(gen['prefix']), gen['text'], grey.format(gen['suffix']), '\n'
# ]))