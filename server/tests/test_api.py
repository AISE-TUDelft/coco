
import warnings
from fastapi.testclient import TestClient
from ..main import app

client = TestClient(app)

def test_homepage():
    response = client.get("/")
    assert response.status_code == 200

def test_verification():
    warnings.warn('TODO: test verification endpoint')
    pass

def test_survey():
    warnings.warn('TODO: test survey endpoint')
    pass

def test_generation():
    ''' 
    Issue a single completion request, end-to-end
    testing the endpoints.
    '''
    pass 

def test_batch_generation():
    ''' 
    Issue a bunch of requests, making sure the time taken 
    is less than the sum of each individual request 
    (i.e. that batching actually works)
    '''
    pass
