# import datetime
# from unittest.mock import MagicMock, patch, AsyncMock

# import os
# import sys
# from uuid import uuid4

# import pytest
# from dotenv import load_dotenv
# from fastapi import FastAPI

# from fastapi.testclient import TestClient
# from starlette.requests import Request

# from models import (
#     GenerateRequest, SurveyRequest, SurveyResponse,
#     GenerateResponse, Session, SessionRequest, ErrorResponse, VerifyRequest, VerifyResponse
# )

# from fastapi.responses import FileResponse

# from models.Requests import SessionEndRequest

# global config
# global mock_chain

# class TestCoCoAPI:

#     @pytest.fixture(scope='function')
#     def client(self):
#         """ Run the FastAPI server with its lifespan context """
#         load_dotenv()

#         mock_completion = MagicMock()
#         global mock_chain
#         mock_chain = MagicMock(return_value='mocked chain behavior')
#         mock_completion.chain = mock_chain

#         with patch.dict('sys.modules', {'completion': mock_completion}):  # mock the completion module
#             from main import app, config as _config
#             global config
#             config = _config

#             with TestClient(app) as client:
#                 yield client

#         # check whether a cache folder exists and delete it even if it's not empty
#         if os.path.exists('cache'):
#             os.system('rm -rf cache')

#     # testing the helper functions

#     @patch('main.get_all_plugin_versions')
#     @patch('main.get_all_programming_languages')
#     @patch('main.get_all_trigger_types')
#     @patch('main.get_all_db_models')
#     def test_cache_tables(self, mock_get_all_db_models, mock_get_all_trigger_types, mock_get_all_programming_languages,
#                           mock_get_all_plugin_versions, client):
#         # setup
#         print("working directory: ", os.getcwd())

#         from main import cache_tables

#         # Arange
#         mock_plugin_versions = [MagicMock(version_name='1.0.0a', version_id=1), MagicMock(version_name='1.0.0b', version_id=2)]
#         mock_programming_languages = [MagicMock(language_name='Python', language_id=1),
#                                       MagicMock(language_name='JavaScript', language_id=2)]
#         mock_trigger_types = [MagicMock(trigger_type_name='man', trigger_type_id=1),
#                               MagicMock(trigger_type_name='auto', trigger_type_id=2)]
#         mock_db_models = [MagicMock(model_name='model_1', model_id=1), MagicMock(model_name='model_2', model_id=2)]

#         mock_get_all_plugin_versions.return_value = mock_plugin_versions
#         mock_get_all_programming_languages.return_value = mock_programming_languages
#         mock_get_all_trigger_types.return_value = mock_trigger_types
#         mock_get_all_db_models.return_value = mock_db_models

#         mock_app = MagicMock()
#         mock_server_db_session = MagicMock()

#         # Act
#         cache_tables(mock_app, mock_server_db_session)

#         # Assert
#         assert mock_app.plugin_versions == {'1.0.0a': 1, '1.0.0b': 2}
#         assert mock_app.languages == {'Python': 1, 'JavaScript': 2}
#         assert mock_app.trigger_types == {'man': 1, 'auto': 2}
#         assert mock_app.llms == {'model_1': 1, 'model_2': 2}

#     def test_request_in_limit_in_limit(self, client):
#         from main import request_in_limit

#         # Arrange
#         mock_session = MagicMock(spec=Session)
#         mock_session.get_session_since.return_value = datetime.datetime.now() - datetime.timedelta(hours=1)
#         mock_session.get_user_request_count.return_value = 200
#         mock_app = MagicMock(spec=FastAPI)
#         mock_app.config = MagicMock()
#         mock_app.config.max_request_rate = 1000

#         # Act / Assert
#         assert request_in_limit(mock_app, mock_session) == True

#     def test_request_in_limit_out_of_limit(self, client):
#         from main import request_in_limit

#         # Arrange
#         mock_session = MagicMock(spec=Session)
#         mock_session.user_id = "test_user_id"
#         mock_session.get_session_since.return_value = datetime.datetime.now() - datetime.timedelta(hours=1)
#         mock_session.get_user_request_count.return_value = 1200
#         mock_app = MagicMock(spec=FastAPI)
#         mock_app.config = MagicMock()
#         mock_app.config.max_request_rate = 1000

#         # Act / Assert
#         assert request_in_limit(mock_app, mock_session) == False


#     def test_request_in_limit_new_session(self, client):
#         from main import request_in_limit

#         # Arrange
#         mock_session = MagicMock(spec=Session)
#         mock_session.get_session_since.return_value = datetime.datetime.now() - datetime.timedelta(minutes=1)
#         mock_session.get_user_request_count.return_value = 0
#         mock_app = MagicMock(spec=FastAPI)
#         mock_app.config = MagicMock()
#         mock_app.config.max_request_rate = 1000

#         # Act / Assert
#         assert request_in_limit(mock_app, mock_session) == True

#     def test_request_in_limit_on_limit(self, client):
#         from main import request_in_limit

#         # Arrange
#         mock_session = MagicMock(spec=Session)
#         mock_session.get_session_since.return_value = datetime.datetime.now() - datetime.timedelta(hours=1)
#         mock_session.get_user_request_count.return_value = 999
#         mock_app = MagicMock(spec=FastAPI)
#         mock_app.config = MagicMock()
#         mock_app.config.max_request_rate = 1000

#         # Act / Assert
#         assert request_in_limit(mock_app, mock_session) == True

#     def test_homepage(self, client):
#         """ Test whether the homepage is accessible """
#         # go one level higher in the directory to have access to the static folder
#         os.chdir('..')  # I literally lost brain cells trying to figure this out

#         response = client.get("/")
#         response2 = client.get("/index.html")

#         assert response.status_code == 200
#         assert response2.status_code == 200
#         assert response.headers['content-type'] == 'text/html; charset=utf-8'
#         assert response2.headers['content-type'] == 'text/html; charset=utf-8'

#     def test_blacklisting_with_invalid_attempts(self, client):
#         # Arrange
#         test_ip = "192.168.1.1"
#         session_req_invalid_token = SessionRequest(user_id="invalid_token", version="1.0.0", project_ide="VSCode",
#                                      project_language="python", user_settings={})
#         session_req_invalid_user = SessionRequest(user_id=str(uuid4()), version="1.0.0", project_ide="VSCode",
#                                         project_language="python", user_settings={})
#         global config
#         maximum_tries = config.max_failed_session_attempts

#         # Act
#         # attempt 1 wih invalid token
#         response = client.post("/api/v3/session/new", json=session_req_invalid_token.model_dump(), headers={"X-Forwarded-For": test_ip})
#         assert response.status_code == 200
#         assert response.json() == ErrorResponse(error='Error getting user by token -> session not created.').model_dump()

#         # attempt 2 with invalid user
#         response = client.post("/api/v3/session/new", json=session_req_invalid_user.model_dump(), headers={"X-Forwarded-For": test_ip})
#         assert response.status_code == 200
#         assert response.json() == ErrorResponse(error='Invalid user token -> session not created.').model_dump()

#         for i in range(maximum_tries - 1): # the reason 1 and not 2 is because invalid tokens are not counted as failed attempts
#             response = client.post("/api/v3/session/new", json=session_req_invalid_user.model_dump(), headers={"X-Forwarded-For": test_ip})
#             assert response.status_code == 200

#         # attempt after blacklisting
#         response_after_blacklist = client.post("/api/v3/session/new", json=session_req_invalid_user.model_dump(), headers={"X-Forwarded-For": test_ip})

#         # Assert
#         assert response.json() == ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.').model_dump()
#         assert response_after_blacklist.json() == ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.').model_dump()

#     def test_after_blacklist_other_endpoints_do_not_work(self, client):
#         # Arrange
#         session_req_invalid_token = SessionRequest(user_id=str(uuid4()), version="1.0.0", project_ide="VSCode",
#                                                    project_language="python", user_settings={})
#         global config
#         maximum_tries = config.max_failed_session_attempts
#         for i in range(maximum_tries + 1):
#             response = client.post("/api/v3/session/new", json=session_req_invalid_token.model_dump())

#         # Act
#         response_session_end = client.post("/api/v3/session/end", json=SessionEndRequest(session_token=str(uuid4())).model_dump())
#         response_verification = client.post("/api/v3/verify", json=VerifyRequest.model_config['json_schema_extra']['examples'][0])
#         response_complete = client.post("/api/v3/complete", json=GenerateRequest.model_config['json_schema_extra']['examples'][0])
#         response_survey = client.post("/api/v3/survey", json=SurveyRequest.model_config['json_schema_extra']['examples'][0])

#         # Assert
#         assert response_session_end.json() == ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.').model_dump()
#         assert response_verification.json() == ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.').model_dump()
#         assert response_complete.json() == ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.').model_dump()
#         assert response_survey.json() == ErrorResponse(error='Access denied. - Blacklisted - Contact us if you think this is a mistake.').model_dump()

#     @patch('main.get_user_by_token')
#     def test_getting_session_for_valid_user_and_check_not_new_session_created_upon_repeated_request(self, mocked_get_user_by_token, client):
#         # Arrange
#         mocked_user = MagicMock()
#         mocked_get_user_by_token.return_value = mocked_user

#         patch('main.app.session_manager.remove_session')

#         session_req = SessionRequest(user_id=str(uuid4()), version="1.0.0", project_ide="VSCode",
#                                                   project_language="python", user_settings={})

#         # Act
#         response = client.post("/api/v3/session/new", json=session_req.model_dump())

#         # Assert
#         assert response.status_code == 200
#         assert response.json()["session_id"] is not None

#         session_id = response.json()["session_id"]

#         response2 = client.post("/api/v3/session/new", json=session_req.model_dump())

#         assert response2.status_code == 200
#         assert response2.json()["session_id"] == session_id


#     def test_end_session_when_session_does_not_exist(self, client):
#         # Arrange
#         session_end_req = SessionEndRequest(session_token=str(uuid4())).model_dump()

#         # Act
#         response = client.post("/api/v3/session/end", json=session_end_req)

#         # Assert
#         assert response.status_code == 200
#         assert response.json() == ErrorResponse(error='Invalid session token -> No session to end.').model_dump()


#     def test_end_session_on_existing_session_works(self, client):
#         # Arrange
#         session_req = SessionRequest(user_id=str(uuid4()), version="1.0.0", project_ide="VSCode",
#                                      project_language="python", user_settings={})
#         with patch('main.get_user_by_token') as mocked_get_user_by_token:
#             mocked_user = MagicMock()
#             mocked_get_user_by_token.return_value = mocked_user
#             response = client.post("/api/v3/session/new", json=session_req.model_dump())
#             session_id = response.json()["session_id"]

#             session_end_req = SessionEndRequest(session_token=session_id).model_dump()

#             # Act
#             response = client.post("/api/v3/session/end", json=session_end_req)

#         # Assert
#         assert response.status_code == 200
#         assert response.json() is None

#     def test_survey(self, client):
#         # Arrange
#         user_id = str(uuid4())
#         session_req = SessionRequest(user_id=user_id, version="1.0.0", project_ide="VSCode",
#                                      project_language="python", user_settings={})
#         with patch('main.get_user_by_token') as mocked_get_user_by_token:
#             mocked_user = MagicMock()
#             mocked_get_user_by_token.return_value = mocked_user
#             response = client.post("/api/v3/session/new", json=session_req.model_dump())
#             session_id = response.json()["session_id"]

#             survey_req = SurveyRequest(session_id=session_id)

#             # Act
#             response = client.post("/api/v3/survey", json=survey_req.model_dump())

#         global config
#         expected_survey_link = config.survey_link.format(user_id=user_id)

#         # Assert
#         assert response.status_code == 200
#         assert response.json() == SurveyResponse(redirect_url=expected_survey_link).model_dump()


#     def test_complete_endpoint_when_one_request_one_generation(self, client):
#         gen_req = GenerateRequest.model_config['json_schema_extra']['examples'][0]
#         with (patch('main.get_session_by_token_if_exists') as mocked_get_session_by_token_if_exists,
#               patch('main.request_in_limit') as mocked_request_in_limit):
#             mocked_session = MagicMock()
#             mocked_get_session_by_token_if_exists.return_value = mocked_session
#             mocked_request_in_limit.return_value = True

#             # define the mocked completion function
#             global mock_chain
#             mock_response = MagicMock(return_value={'model_1': 'np.array(items)'})
#             mock_chain.invoke = mock_response

#             response = client.post('api/v3/complete', json=gen_req)

#         assert response.status_code == 200
#         for key in response.json()["completions"]:
#             assert len(response.json()["completions"][key]) > 0

#     def test_complete_endpoint_when_generation_throws(self, client):
#         gen_req = GenerateRequest.model_config['json_schema_extra']['examples'][0]
#         with (patch('main.get_session_by_token_if_exists') as mocked_get_session_by_token_if_exists,
#               patch('main.request_in_limit') as mocked_request_in_limit):
#             mocked_session = MagicMock()
#             mocked_get_session_by_token_if_exists.return_value = mocked_session
#             mocked_request_in_limit.return_value = True

#             # define the mocked completion function
#             global mock_chain
#             mock_response = MagicMock(return_value={'model_1': 'np.array(items)'})
#             mock_chain.invoke = mock_response
#             mock_response.side_effect = Exception('mocked exception')

#             response = client.post('api/v3/complete', json=gen_req)

#         assert response.status_code == 200
#         assert response.json()['error'] == 'Error generating completions.'

#     def test_verification_of_active_request(self, client):
#         with patch('main.get_session_by_token_if_exists') as mocked_get_session_by_token_if_exists:
#             # Arrange
#             mocked_session = MagicMock()
#             mocked_get_session_by_token_if_exists.return_value = mocked_session
#             mocked_session.update_active_request.return_value = True

#             # Act
#             response_true = client.post('api/v3/verify', json=VerifyRequest.model_config['json_schema_extra']['examples'][0])

#             # Arrange
#             mocked_session.update_active_request.return_value = False

#             # Act
#             response_false = client.post('api/v3/verify', json=VerifyRequest.model_config['json_schema_extra']['examples'][0])

#         # Assert
#         assert response_true.status_code == 200
#         assert response_false.status_code == 200
#         assert response_true.json() == VerifyResponse(success=True).model_dump()
#         assert response_false.json() == VerifyResponse(success=False).model_dump()


#     def test_websocket_generate_endpoint_with_one_request(self, client):
#         # Arrange
#         gen_req = GenerateRequest.model_config['json_schema_extra']['examples'][0]
#         with (patch('main.get_session_by_token_if_exists') as mocked_get_session_by_token_if_exists,
#               patch('main.autocomplete_v3') as mocked_completion_generator):
#             # Arrange
#             mocked_session = MagicMock()
#             mocked_get_session_by_token_if_exists.return_value = mocked_session
#             mocked_completion_generator.return_value = GenerateResponse(completions={'model_1': 'np.array(items)'}, time=0.1)

#             # establish a websocket connection
#             with client.websocket_connect('/api/v3/ws/complete') as websocket:
#                 # Act
#                 websocket.send_json(gen_req)
#                 response = websocket.receive_json()

#                 # Assert
#                 assert response['completions'] is not None
#                 assert response['time'] is not None
#                 assert response['completions']['model_1'] == 'np.array(items)'
#                 assert response['time'] == 0.1

#     def test_having_two_generations_with_same_websocket_connection(self, client):
#         # Arrange
#         gen_req = GenerateRequest.model_config['json_schema_extra']['examples'][0]
#         with (patch('main.get_session_by_token_if_exists') as mocked_get_session_by_token_if_exists,
#               patch('main.autocomplete_v3') as mocked_completion_generator):
#             # Arrange
#             mocked_session = MagicMock()
#             mocked_get_session_by_token_if_exists.return_value = mocked_session
#             mocked_completion_generator.return_value = GenerateResponse(completions={'model_1': 'np.array(items)'}, time=0.1)

#             # establish a websocket connection
#             with client.websocket_connect('/api/v3/ws/complete') as websocket:
#                 # Act
#                 websocket.send_json(gen_req)
#                 response = websocket.receive_json()

#                 # Assert
#                 assert response['completions'] is not None
#                 assert response['time'] is not None
#                 assert response['completions']['model_1'] == 'np.array(items)'
#                 assert response['time'] == 0.1

#                 # Arrange
#                 mocked_completion_generator.return_value = GenerateResponse(completions={'model_2': 'np.array(items2)'}, time=0.2)

#                 # Act
#                 websocket.send_json(gen_req)
#                 response = websocket.receive_json()

#                 # Assert
#                 assert response['completions'] is not None
#                 assert response['time'] is not None
#                 assert response['completions']['model_2'] == 'np.array(items2)'
#                 assert response['time'] == 0.2


#     def test_verifying_requests_through_websocket(self, client):
#         # Arrange
#         with (patch('main.get_session_by_token_if_exists') as mocked_get_session_by_token_if_exists,
#               patch('main.verify_v3') as mocked_verify_v3):
#             mocked_session = MagicMock()
#             mocked_get_session_by_token_if_exists.return_value = mocked_session
#             mocked_session.update_active_request.return_value = True

#             mocked_verify_v3.return_value = VerifyResponse(success=True)

#             # Act
#             with client.websocket_connect('/api/v3/ws/verify') as websocket:
#                 websocket.send_json(VerifyRequest.model_config['json_schema_extra']['examples'][0])
#                 response = websocket.receive_json()

#         # Assert
#         assert response['success'] == True


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