import warnings

from fastapi.testclient import TestClient
from ..main import app, config

client = TestClient(app)

from ..models.Requests import GenerateRequest, SurveyRequest
from ..models.Responses import SurveyResponse
from ..models.Types import TriggerType, LanguageType, IDEType

def test_homepage():
    ''' Test whether the homepage is accessible '''
    response = client.get("/")
    assert response.status_code == 200

def test_verification():
    warnings.warn('TODO: test verification endpoint')
    pass

def test_survey():
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
    pass

def test_batch_generation():
    ''' 
    Issue a bunch of requests, making sure the time taken 
    is less than the sum of each individual request 
    (i.e. that batching actually works)

    TODO: We need florimondmanca/asgi-lifespan to correctly set up the 
    lifespan, according to  https://fastapi.tiangolo.com/advanced/async-tests/
    '''
    pass

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