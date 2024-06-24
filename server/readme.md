# CoCo Server

- [`api`](./api) contains the exposed api and request logic 
- [`database`](./database) contains database-related backend models and logic.
- [`static`](./static) are static resources like the splash page.
- [`tests`](./tests) contains our tests, of course!

#### Installation 
> [!NOTE]
> `vllm`, our inference engine, is supported only on Linux and direct installations assume CUDA 12.1 for its precompiled kernels. 

With Python `3.11` ([requirement in `vllm`](https://docs.vllm.ai/en/stable/getting_started/installation.html)), install via 

```py
pip install -r requirements.txt
```

#### Running
To run the server, use 

```py
# TODO: update this to pass in the correct survey_link and db_url
fastapi dev main.py
```

