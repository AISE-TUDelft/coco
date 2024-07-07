# CoCo Server

- [`completion`](./completion) handles LLM-inference logic.
- [`database`](./database) contains data models for storage & network.
- [`static`](./static) are static resources like the splash page.
- [`tests`](./tests) contains our tests, of course!

#### Installation 
> [!NOTE]
> `vllm`, our inference engine, is supported only on Linux and direct installations assume CUDA 12.1 for its precompiled kernels. 

With Python `3.11` ([requirement in `vllm`](https://docs.vllm.ai/en/stable/getting_started/installation.html)), install via 

```bash
pip install -r requirements.txt
```

#### Running
To run the server, use 

```bash
# TODO: update this to pass in the correct survey_link and db_url
fastapi dev main.py
```

---

## Requirements for RAG (patch 1)

As this patch introduces the capability to have prompts be enhanced through RAG (Retrieval-Augmented Generation),
you will need to install the `pgvector` extension for postgres.

*A thorough explanation of the installation process can be found [here](https://github.com/pgvector/pgvector)*
##### Installation (Linux & Mac)
```bash
cd /tmp
git clone --branch v0.7.2 https://github.com/pgvector/pgvector.git
cd pgvector
make
make install # may need sudo
```