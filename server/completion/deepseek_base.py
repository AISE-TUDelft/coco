'''
Interactions with Deepseek-base-1.3b
'''

''' 
DeepSeek-Coder v1. Paper: https://arxiv.org/pdf/2401.14196
Base models are trained with FIM, Instruct are fine-tuned to follow instructions (no FIM). 

DeepSeek-Coder v2 paper: https://github.com/deepseek-ai/DeepSeek-Coder-V2/blob/main/paper.pdf
StarCoder2 paper: https://arxiv.org/pdf/2402.19173

            Params  HumanEval   MBPP    FIM (Allal et al. 2023)
Base        1.3B    28%         46%     70%
Base        6.7B    45%         61%     81%
Base        33B     50%         66%     81%
Instruct    1.3B    48%         50%     -
Instruct    6.7B    66%         65%     -
Instruct    33B     69%         70%     -

StableCode  3B      -           -       65%
StarV2      3B      31%         57%     69%
StarV2      7B      35%         54%     73%
StarV2      15B     46%         66%     70%
CodeLlama   13B     -           -       80%
DS-V2-Base  16/2.4B -           -       on par w DS-V1-6.7B

Observations: 
StarCoder-16B (v1) achieves similar FIM as DeepSeek-Base-1B (in DS-v2 paper). 
DeepSeek-Coder-6.7B seems like a really good model.  

While DeepSeek V2 models seem promising, I'm not sure how request-batching fares
in a MoE model, so I leave that for later. The V1-6.7B model seems ideal in terms of simplicity.

To best leverage FIM, we should use a Base model (as opposed to Instruct). 
'''

from langchain_core.prompts import PromptTemplate
from .vllm_modified import VLLM_M 
# TODO: consider changing relative import to absolute by importing server as package

'''
TEMPLATES. DeepSeek-Coder (v1) base models are finetuned on two 
(disjoint) types of completion. 

1. Code Insertion (FIM)
2. Repo-level Code Completion 

# TODO: Repo-level code completion is useful with RAG. 
# I'm sticking to FIM for now. 
'''

# not the actual | characters, but U+ff5c
template = '''<｜fim▁begin｜>{prefix}<｜fim▁hole｜>{suffix}<｜fim▁end｜>'''
prompt = PromptTemplate.from_template(template)

''' 
VLLM Engine. Supported features: 
1. Tensor parallelism (multi-GPU inference)
2. AWQ Quantisation (3/4 bit, 3.2x speedup, 
    see https://github.com/mit-han-lab/llm-awq)
3. Automatic Prefix Caching (APC) for long-document queries 
    and multi-round conversation. 
'''

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

llm_chain = prompt | llm 
