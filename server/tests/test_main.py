import pytest

from fastapi.testclient import TestClient
from ..main import app
from ..models import (
    GenerateRequest, SurveyRequest, SurveyResponse,
    CoCoConfig
)

config = CoCoConfig()

@pytest.fixture(scope='session')
def client(): 
    ''' Run the FastAPI server with its lifespan context '''
    with TestClient(app) as client:
        yield client

def test_homepage(client):
    ''' Test whether the homepage is accessible '''
    response = client.get("/")
    assert response.status_code == 200

def test_verification(client):
    raise NotImplementedError('TODO: test the verification endpoint')

def test_survey(client):
    ''' 
    Check we can send a SurveyRequest and parse 
    the response as a SurveyResponse. 
    '''
    # might as well test with the API examples right
    example_req = SurveyRequest.model_config['json_schema_extra']['examples'][0]
    user_id = example_req['user_id']
    survey_link = config.survey_link.format(user_id=user_id)

    response = client.post('api/v3/survey', 
                        json=SurveyRequest(user_id=user_id).model_dump())

    assert response.status_code == 200
    response = SurveyResponse(**response.json())
    assert response.redirect_url == survey_link


def test_generation():
    ''' 
    Issue a single completion request, end-to-end
    testing the endpoints.
    '''
    # FastAPI context managers require you to wrap it before you tap it 
    # in a test https://fastapi.tiangolo.com/advanced/testing-events/
    # TODO: refactor this to a setup/teardown fixture somehow.
    with TestClient(app) as client:

        gen_req = GenerateRequest.model_config['json_schema_extra']['examples'][0]
        json = GenerateRequest(**gen_req | {'store': False}).model_dump()
        response = client.post('api/v3/complete', json=json)

        assert response.status_code == 200
        assert len(response.json()['completions']) > 0

        # TODO: let's also assert that these things are in fact stored
        json = GenerateRequest(**gen_req | {'store': True})
        raise NotImplementedError('TODO: test that the request is stored')

def test_generation_is_not_stored():
    ''' 
    Issue a single completion request, end-to-end
    testing the endpoints, but with the `store` flag set to False
    '''
    raise NotImplementedError('TODO: test that the request is not stored')


def test_batch_generation():
    ''' 
    Issue a bunch of requests, making sure the time taken 
    is less than the sum of each individual request 
    (i.e. that batching actually works)

    TODO: We need florimondmanca/asgi-lifespan to correctly set up the 
    lifespan, according to  https://fastapi.tiangolo.com/advanced/async-tests/
    '''
    raise NotImplementedError('TODO: test that the time taken is less than the sum of each individual request')


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