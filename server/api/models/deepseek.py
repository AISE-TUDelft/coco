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

from langchain.chains import LLMChain
from langchain_community import VLLM 
from langchain_core.prompts import PromptTemplate

'''
TEMPLATES. DeepSeek-Coder (v1) base models support (disjoint) two types of completion:
1. Code Insertion (FIM)
2. Repo-level Code Completion 

# TODO: Repo-level code completion is useful with RAG. I'm sticking to FIM for now. 
'''

template = '''<|fim_begin|>{prefix}<|fim_hole|>{suffix}<|fim_end|>'''
prompt = PromptTemplate.from_template(template)

''' 
VLLM Engine. Supported features: 
1. Tensor parallelism (multi-GPU inference)
2. AWQ Quantisation (3/4 bit, 3.2x speedup, see https://github.com/mit-han-lab/llm-awq)
'''

llm = VLLM(
    model_name='deepseek-ai/deepseek-coder-1.3b-base',
    trust_remote_code=True, 
)

llm_chain = LLMChain(prompt=prompt, llm=llm)

# to manually test this file by running it
if __name__ == '__main__':
    print(llm_chain.invoke('What is the capital of france?'))
