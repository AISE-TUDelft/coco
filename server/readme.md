# CoCo Server

- [`api`](./api) contains the exposed api and request logic 
- [`database`](./database) contains database-related backend models and logic.
- [`static`](./static) are static resources like the splash page.
- [`tests`](./tests) contains our tests, of course!

#### Installation 
With Python `3.12`, install via 

```py
pip install -r requirements.txt
```

#### Running
To run the server, use 

```py
# TODO: probably should update this to pass in the correct survey_link and db_url
fastapi dev main.py
```

