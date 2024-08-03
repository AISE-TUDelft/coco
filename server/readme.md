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

## Installation of PostgreSQL (Linux)
```bash
sudo apt update
sudo apt install gnupg2 wget nano

sudo apt install lsb-release
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
sudo apt update

sudo apt install postgresql-16 postgresql-contrib-16

sudo systemctl start postgresql
sudo systemctl enable PostgreSQL
# Or in case of absence of systemctl (as in case of Docker containers on Ronaldo):
# sudo service postgresql start
 
```

You can then create a user and database for the project.
Here, as the default for the project given the .env, files, code, etc., we use `postgres` (default user) as the user and password and `coco` as the actual database name and `coco_test` for the test database.

```bash
sudo -u postgres psql postgres

>>> \password postgres
>>> Enter new password: postgres
>>> Enter it again: postgres
>>> exit

sudo -u postgres createdb coco
sudo -u postgres createdb coco_test
```
to ensure that the database is created, you can run the database tests in the `tests` directory.

```bash
pytest tests/test_sqlalchemy_model.py
```
#### Running
To run the server, use 

```bash
# TODO: update this to pass in the correct survey_link and db_url
fastapi dev main.py
```

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

#### Running
To run the server, use 

```bash
# TODO: update this to pass in the correct survey_link and db_url
fastapi dev main.py
```

