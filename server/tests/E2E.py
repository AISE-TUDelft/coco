import os
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime

import pytest
from dotenv import load_dotenv
from sqlalchemy.orm import Session as sql_session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from database.crud import create_user, get_user_by_token
from database.db_schemas import UserCreate
from models import SessionRequest, CoCoConfig, GenerateRequest, VerifyRequest
from models.Requests import SessionEndRequest
from tests import create_fresh_database

global db_session

load_dotenv()
global config
config = CoCoConfig()

global mock_chain


class TestEndToEnd:

    @pytest.fixture(scope="session")
    def db_session(self):
        engine = create_engine(config.test_database_url)
        create_fresh_database(engine)
        yield sessionmaker(autocommit=False, autoflush=False, bind=engine)
        create_fresh_database(engine)
        engine.dispose()

    @pytest.fixture(scope="function")
    def client(self, db_session: sessionmaker[sql_session]):
        # TODO: remove the mocking behavior and use the actual completion chain when fully implemented
        mock_completion = MagicMock()
        global mock_chain
        mock_chain = MagicMock()
        mock_completion.chain = mock_chain

        with patch.dict("sys.modules", {"completion": mock_completion}):
            with patch("main.get_db") as mock_get_db:
                mock_get_db.return_value = db_session()

                from main import app, config as _config

                global config
                config = _config

                with TestClient(app) as client:
                    yield client

        # check whether a cache folder exists and delete it even if it's not empty
        if os.path.exists("cache"):
            os.system("rm -rf cache")

    @pytest.fixture(scope="function")
    def db_transaction(self, db_session: sessionmaker[sql_session]):
        session = db_session()
        connection = session.connection()
        transaction = connection.begin_nested()

        session.begin_nested()

        yield session

        transaction.rollback()
        connection.close()
        session.close()

    def test_an_entire_interaction_cycle(self, db_transaction, client):
        # create a user
        user_token = str(uuid4())
        user_joined_at = datetime.now(tz=datetime.now().astimezone().tzinfo)
        user = UserCreate(token=user_token, joined_at=str(user_joined_at))

        # add the user to the database
        create_user(db_transaction, user)

        # have the user request a new session
        session_req = SessionRequest(
            user_id=user_token,
            version="0.0.1v",
            project_ide="VSCode",
            project_language="python",
            user_settings={
                "store_completions": True,
                "store_context": True,
                "ask_for_feedback": True,
            },
        )
        session_response = client.post(
            "/api/v3/session/new", json=session_req.model_dump()
        )

        assert (
            session_response.status_code == 200
        )  # check if the request was successful
        session_id = session_response.json()["session_id"]

        # have the user request a generation
        request_id = str(uuid4())
        generate_req = GenerateRequest.model_validate(
            {
                "session_id": session_id,
                "request_id": request_id,
                "prefix": "import numpy as np\n\ndef main(): \n    items = [1,2,3]\n\n    # convert items to numpy array \n    arr = ",
                "suffix": "\n\n    # get the data type\n    print(arr.dtype)",
                "trigger": "auto",
                "language": "python",
                "telemetry": {
                    "time_since_last_completion": 1000,
                    "typing_speed": 100,
                    "document_length": 1000,
                    "cursor_relative_position": 0.5,
                },
                "timestamp": "2021-08-01T12:00:00",
            }
        )
        if isinstance(generate_req.timestamp, datetime):
            generate_req.timestamp = generate_req.timestamp.isoformat()

        # define the mocked behavior of the completion chain
        # TODO: also remove this
        global mock_chain
        mock_response = MagicMock(return_value={"deepseek-1.3b": "np.array(items)"})
        mock_chain.invoke = mock_response

        generation_response = client.post(
            "/api/v3/complete", json=generate_req.model_dump()
        )

        assert generation_response.status_code == 200
        generation_response_json = generation_response.json()
        assert generation_response_json["time"] is not None
        assert generation_response_json["completions"] is not None
        for key in generation_response_json["completions"].keys():
            assert generation_response_json["completions"][key] is not None

        # have the user request verify a previous completion
        verify_req = VerifyRequest.model_validate(
            {
                "session_token": session_id,
                "verify_token": request_id,
                "chosen_model": list(generation_response_json["completions"].keys())[0],
                "shown_at": {
                    list(generation_response_json["completions"].keys())[0]: [
                        "2021-08-01T12:00:00",
                        "2021-08-01T12:00:05",
                    ]
                },
                "ground_truth": [
                    ("2021-08-01T12:00:00", "np.array(items)"),
                    ("2021-08-01T12:00:05", "np.array(items)"),
                    ("2021-08-01T12:00:10", "np.array(items)"),
                ],
            }
        )
        for key in verify_req.shown_at.keys():
            for i in range(len(verify_req.shown_at[key])):
                verify_req.shown_at[key][i] = verify_req.shown_at[key][i].isoformat()
        for i in range(len(verify_req.ground_truth)):
            verify_req.ground_truth[i] = (
                verify_req.ground_truth[i][0].isoformat(),
                verify_req.ground_truth[i][1],
            )
        verify_response = client.post("/api/v3/verify", json=verify_req.model_dump())

        assert verify_response.status_code == 200
        assert verify_response.json()["success"]

        # have the user end a session
        end_session_req = SessionEndRequest.model_validate(
            {"session_token": session_id}
        )
        end_session_response = client.post(
            "/api/v3/session/end", json=end_session_req.model_dump()
        )

        assert end_session_response.status_code == 200
        assert end_session_response.json() is None

        # ensure that the user's data is stored in the database
        user = get_user_by_token(db_transaction, user_token)
        user_queries = user.queries
        assert user_queries is not None
        assert len(user_queries) == 1
        query = user_queries[0]
        assert query is not None
        assert str(query.query_id) == str(request_id)
        query_telemetry = query.telemetry
        assert query_telemetry is not None
        query_context = query.context
        assert query_context is not None
        query_ground_truths = query.ground_truths
        assert query_ground_truths is not None
        assert len(query_ground_truths) == 3
        query_completions = query.had_generations
        assert query_completions is not None
        assert len(query_completions) == 1
