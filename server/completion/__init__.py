'''
Constructs the whole LLM chain. 
Takes GenerateRequest as input, and returns a dict consisting 
of each model's completion to be used in GenerateReponse.
'''

from langchain_core.runnables import RunnableLambda
from langchain_core.outputs import Generation

from .deepseek_base import llm_chain as deepseek
# from .starcoder_2

# models is a dict coerced to a RunnableParallel
models = {
    'deepseek-1.3b': deepseek.invoke
}

input_parser = RunnableLambda(
    lambda x: {'prefix': x.prefix, 'suffix': x.suffix}
)

def output_handler(generations: dict[str, Generation]) -> dict[str, str]:
    ''' 
    Parse output of each model into a string, and TODO: save it to the database. 
    '''
    return {model: generation.text for model, generation in generations.items()}

output_handler = RunnableLambda(output_handler)

chain = input_parser | models | output_handler

