import datetime
from uuid import uuid4

import pytest
from unittest.mock import patch, MagicMock

from database.app_to_db import (get_query_from_request, get_context_from_request,
                                get_generation_from_request, get_telemetry_from_request,
                                get_ground_truths_from_request, add_active_request_to_db)
from models import IDEType, LanguageType, GenerateRequest, TriggerType
from models.Requests import Telemetry

from models.Sessions import Session as SessionModel
from models.Lifecycle import ActiveRequest, ModelCompletionDetails

from typing import Tuple

def get_dummy_active_request_and_session() -> Tuple[ActiveRequest, SessionModel]:
    session_id = str(uuid4())
    user_id = str(uuid4())
    request_id = str(uuid4())
    request_time = datetime.datetime.now()
    active_request = ActiveRequest.model_validate({
            "request": GenerateRequest.model_validate({
                    "session_id": session_id,
                    "request_id": request_id,
                    "prefix": "Hello, my name is",
                    "suffix": "Shady",
                    "trigger": TriggerType("auto"),
                    "language": LanguageType("python"),
                    "telemetry": Telemetry.model_validate({
                        "time_since_last_completion": 1000,
                        "typing_speed": 100,
                        "document_length": 1000,
                        "cursor_relative_position": 0.5
                    }),
                    "timestamp": request_time
                }),
            "completions": {
                "model_1": ModelCompletionDetails.model_validate({
                    "completion": "Slim",
                    "shown_at": [(request_time + datetime.timedelta(seconds=t)) for t in range(1, 61, 10)],
                    "accepted": True
                }),
                "model_2": ModelCompletionDetails.model_validate({
                    "completion": "Slime",
                    "shown_at": [request_time + datetime.timedelta(seconds=10)],
                    "accepted": False
                }),
            },
            "time_taken": 100,
            "ground_truth": [
                ((request_time + datetime.timedelta(seconds=10)), "Slim"),
                ((request_time + datetime.timedelta(seconds=30)), "Slime")
            ]
        })

    active_session = SessionModel(user_id=user_id, project_primary_language=LanguageType("python"),
                                  project_ide=IDEType("VSCode"), user_settings=None, db_session=None,
                                  project_coco_version="1.0.0")

    active_session.get_user_active_requests()[request_id] = active_request

    return active_request, active_session

class TestAppToDb:
    @pytest.fixture
    def app(self):
        with patch('main.app') as app:
            app.languages = {'python': 1}
            app.trigger_types = {'auto': 1}
            app.plugin_versions = {'1.0.0': 1}
            app.llms = {'model_1': 1, 'model_2': 2}
            app.config.server_version_id = 1
            yield app

    def test_get_context_from_request(self, app):
        #Arrange
        active_request, _ = get_dummy_active_request_and_session()

        # Act
        context = get_context_from_request(active_request, "1.0.0", app)

        # Assert
        assert context.prefix == "Hello, my name is"
        assert context.suffix == "Shady"
        assert context.trigger_type_id == 1
        assert context.language_id == 1
        assert context.version_id == 1

    def test_get_telemetry_from_request(self):
        #Arrange
        active_request, _ = get_dummy_active_request_and_session()

        # Act
        telemetry = get_telemetry_from_request(active_request)

        # Assert
        assert telemetry.time_since_last_completion == 1000
        assert telemetry.typing_speed == 100
        assert telemetry.document_char_length == 1000
        assert telemetry.relative_document_position == 0.5


    def test_get_query_from_request(self, app):
        #Arrange
        active_request, active_session = get_dummy_active_request_and_session()
        context = get_context_from_request(active_request, "1.0.0", app)
        telemetry = get_telemetry_from_request(active_request)

        # Act
        query = get_query_from_request(active_request, context, telemetry, active_session.get_user_id(), app)

        # Assert
        assert query.query_id == active_request.request.request_id
        assert query.user_id == active_session.get_user_id()
        assert query.telemetry_id == telemetry.telemetry_id
        assert query.context_id == context.context_id
        assert query.total_serving_time == 100
        assert query.timestamp == str(active_request.request.timestamp)
        assert query.server_version_id == 1


    def test_get_ground_truths_from_request(self, app):
        #Arrange
        active_request, _ = get_dummy_active_request_and_session()
        context = get_context_from_request(active_request, "1.0.0", app)
        telemetry = get_telemetry_from_request(active_request)
        query = get_query_from_request(active_request, context, telemetry, "user_id", app)

        # Act
        ground_truths = get_ground_truths_from_request(active_request, query)

        # Assert
        assert len(ground_truths) == 2
        assert ground_truths[0].ground_truth == "Slim"
        assert ground_truths[0].truth_timestamp == str(active_request.request.timestamp + datetime.timedelta(seconds=10))
        assert ground_truths[1].ground_truth == "Slime"
        assert ground_truths[1].truth_timestamp == str(active_request.request.timestamp + datetime.timedelta(seconds=30))


    def test_get_generation_from_request(self, app):
        # Arrange
        active_request, _ = get_dummy_active_request_and_session()
        context = get_context_from_request(active_request, "1.0.0", app)
        telemetry = get_telemetry_from_request(active_request)
        query = get_query_from_request(active_request, context, telemetry, "user_id", app)

        # Act
        generations = get_generation_from_request(active_request, query, app)

        # Assert
        assert len(generations) == 2
        for i in range(2):
            assert generations[i].query_id == query.query_id
            assert generations[i].model_id == i + 1
            assert generations[i].completion == active_request.completions[f"model_{i + 1}"].completion
            assert generations[i].shown_at == [str(x) for x in active_request.completions[f"model_{i + 1}"].shown_at]
            assert generations[i].was_accepted == active_request.completions[f"model_{i + 1}"].accepted
            # assert generations[i].confidence == 1.0
            # assert generations[i].logprobs == [0.2, 0.3, 0.4, 0.1]

    # the add_active_request_to_db function is not tested as the individual components are alredy tested
    # and the creation of the tables by the objects are tested in test_database.py