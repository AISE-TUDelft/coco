from .deepseek_base import llm_chain as deepseek

Models = {deepseek.__module__: deepseek.ainvoke}