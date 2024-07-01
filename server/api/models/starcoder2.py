
from langchain_community.llms.vllm import VLLM
from langchain_core.prompts import PromptTemplate

# TODO: StarCoder2 supports repo-level FIM 
# this requires dynamic template based on how many files are included. 
template='''<repo_name>{reponame}<file_sep>{filepath}
{code0}<file_sep><fim_prefix>{filepath1}
{code1_pre}<fim_suffix>{code1_suf}<fim_middle>'''
prompt = PromptTemplate.from_template(template)


