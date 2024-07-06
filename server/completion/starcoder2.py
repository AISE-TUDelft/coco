
from vllm_modified import VLLM_M 
from langchain_core.prompts import PromptTemplate

# TODO: StarCoder2 supports repo-level FIM 
# this requires dynamic template based on how many files are included. 
# template='''<repo_name>{reponame}<file_sep>{filepath}
# {code0}<file_sep><fim_prefix>{filepath1}
# {code1_pre}<fim_suffix>{code1_suf}<fim_middle>'''
# prompt = PromptTemplate.from_template(template)

llm = VLLM_M(
    model='deepseek-ai/deepseek-coder-1.3b-base',
    trust_remote_code=True, 

    logprobs=1, # TODO: this variable is not used at all...

    # HYPERPARAMETERS (FOR AB STUDYYYYY)
    vllm_kwargs=dict(
        max_model_len= 10_000,          # default 65536 at 0.9 utilisation
        quantization = None,            # awq, gptq, squeezellm, and fp8
        gpu_memory_utilization = 0.9,   # default
        swap_space = 4,                 # swap space in GiB to use when 'best_of' sampling > 1
        enforce_eager = False,          # use CUDA Graphs to reduce CPU-GPU communication: https://pytorch.org/blog/accelerating-pytorch-with-cuda-graphs/
        max_seq_len_to_capture = 8192,  # Max seq length covered by CUDA graph. Larger falls back to eager mode.
    ),           
    temperature=0,          # default 1.0. how random the generations are 
    top_p=0.25,             # what percentage of tokens to consider 
    presence_penalty=1.0    # penalise new tokens based on their frequency in the generated text so far
)


# NOTE: leaving two functions here in case it's useful for future testing
pre, suf = '''
import numpy as np

def main(): 
    items = [1,2,3]

    # convert items to numpy array 
    arr = ｜

    # get the data type
    print(arr.dtype)

'''.strip().split('｜')

# helper for debugging what is generated exactly in FIM
grey = '\033[90m{}\033[0m'
print_fim = lambda gen: print(''.join([
    grey.format(gen['prefix']), gen['text'], grey.format(gen['suffix']), '\n'
]))
if __name__ == '__main__':
    print(llm.invoke(pre))

