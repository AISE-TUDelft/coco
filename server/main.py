from fastapi import FastAPI
from starlette.responses import FileResponse

from api.api import router as v3_router

app = FastAPI(
    title='CoCo API',
    description='RESTful API that provides code completion services to the CoCo IDE plugin.',
    version='0.0.1',
)

app.include_router(v3_router, prefix='/api/v3')


@app.get('/')
@app.get('/index.html')
async def root():
    return FileResponse('./static/index.html')

# @app.get('/')
# async def root():
#     return {'message': 'Hello World'}
#
#
# @app.get('/hello/{name}')
# async def say_hello(name: str):
#     return {'message': f'Hello {name}'}
