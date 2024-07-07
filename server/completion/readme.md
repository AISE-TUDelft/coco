
#### `completion`
Completion generation logic for each LLM that we support. 

###### Usage 
You can import a LangChain `Runnable` to provide inputs as follows:

```python
from completion import chain 
from models import GenerateRequest

def generate(gen_req: GenerateRequest):
    completions: dict[str, str] = chain.invoke(gen_req)
    return completions
```