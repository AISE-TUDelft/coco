import datetime
import threading
import time
from logging import Logger
from typing import Tuple
from uuid import uuid4

import pytest
from unittest.mock import patch, MagicMock

from fastapi import FastAPI

from models import IDEType, LanguageType, GenerateRequest, TriggerType
from models.Requests import Telemetry, VerifyRequest

from models.Sessions import Session as SessionModel
from models.Lifecycle import ActiveRequest, ModelCompletionDetails
from models.Sessions import Session, SessionManager, UserSetting, delete_expired_sessions
from sqlalchemy.orm.session import Session as DBSession

def get_dummy_active_request_and_session(session: Session) -> Tuple[str, GenerateRequest, dict, float, ActiveRequest]:
    session_id = str(uuid4())
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

    request = GenerateRequest.model_validate({
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
    })

    completions = {
        "model_1": "Slim",
        "model_2": "Slime"
    }

    time_taken = 0.1

    verify_request = VerifyRequest.model_validate({
        "session_token": session_id,
        "verify_token": request_id,
        "chosen_model": "model_1",
        "shown_at": {
            "model_1": [(request_time + datetime.timedelta(seconds=t)) for t in range(1, 61, 10)],
            "model_2": [(request_time + datetime.timedelta(seconds=10))]
        },
        "ground_truth": [
                ((request_time + datetime.timedelta(seconds=10)), "Slim"),
                ((request_time + datetime.timedelta(seconds=30)), "Slime")
            ]
    })

    return request_id, request, completions, time_taken, active_request, verify_request


class TestSessions:
    session = None

    @pytest.fixture
    def base_session(self):
        self.session = Session(user_id= str(uuid4()), project_primary_language=LanguageType("python"),
                 project_ide= IDEType("VSCode"), user_settings={}, db_session=None,
                 project_coco_version="1.0.0")


    def test_session_creation(self, base_session):
        assert len(self.session.get_user_active_requests()) == 0
        assert len(self.session.get_user_settings().keys()) != 0
        assert self.session.get_user_request_count() == 0
        assert self.session.get_expiration_timestamp() is None

    def test_adding_active_request(self, base_session):
        # Arrange
        request_id, request, completions, time_taken, active_request, verify_request\
            = get_dummy_active_request_and_session(self.session)

        # Act
        self.session.add_active_request(request_id, request, completions, time_taken)

        # Assert
        assert len(self.session.get_user_active_requests()) == 1
        stored_active_request = self.session.get_active_request(request_id)
        assert stored_active_request.request == request
        assert len(stored_active_request.completions.keys()) == 2
        for model_name, completion in completions.items():
            assert stored_active_request.completions[model_name].completion == completion
            assert stored_active_request.completions[model_name].accepted == False
            assert stored_active_request.completions[model_name].shown_at == []
        assert stored_active_request.time_taken == 100
        assert stored_active_request.ground_truth == []

    def test_adding_active_request_then_verifying_it(self, base_session):
        # Arrange
        request_id, request, completions, time_taken, active_request, verify_request\
            = get_dummy_active_request_and_session(self.session)

        # Act
        self.session.add_active_request(request_id, request, completions, time_taken)
        self.session.update_active_request(request_id, verify_request)
        stored_active_request = self.session.get_active_request(request_id)

        # Assert
        assert stored_active_request.request == request # Request should not be modified
        assert len(stored_active_request.completions.keys()) == 2
        for model_name, completion in completions.items():
            assert stored_active_request.completions[model_name].completion == completion
            assert stored_active_request.completions[model_name].accepted == (verify_request.chosen_model == model_name)
            assert stored_active_request.completions[model_name].shown_at == verify_request.shown_at[model_name]
        assert stored_active_request.ground_truth == verify_request.ground_truth


    # the functionality for dumping the session to the database is tested in the test_sessions_manager.py file
    # the actual call to the function however is not tested here as that would more so constitute an integration test


class TestSessionManager:
    session = None

    @pytest.fixture
    def base_session(self):
        self.session = Session(user_id=str(uuid4()), project_primary_language=LanguageType("python"),
                               project_ide=IDEType("VSCode"), user_settings={}, db_session=None,
                               project_coco_version="1.0.0")

    @pytest.fixture
    def base_session_manager(self):
        return SessionManager(default_session_duration=1800) # 30 minutes

    def test_session_manager_creation(self, base_session_manager):
        assert len(base_session_manager.get_sessions()) == 0
        assert base_session_manager.get_current_timeslot() == 0
        assert len(base_session_manager.get_timers()) == 0
        assert len(base_session_manager.get_user_to_session()) == 0

    def test_adding_session_to_session_manager(self, base_session_manager, base_session):
        # Act
        returned_session_id = base_session_manager.add_session(self.session)

        # Assert
        assert self.session.get_expiration_timestamp() is not None  # Expiration timestamp should be set -> Logic could change in the session manager of what the calculation is -> it suffice to check that it is not None
        assert len(base_session_manager.get_sessions()) == 1
        assert base_session_manager.get_sessions()[returned_session_id] == self.session
        assert len(base_session_manager.get_user_to_session()) == 1
        assert base_session_manager.get_user_to_session()[self.session.get_user_id()] == returned_session_id

    def test_adding_session_to_session_manager_and_deleting_it(self, base_session_manager, base_session, mocker):
        # Arrange
        app = MagicMock(spec=FastAPI)
        logger = MagicMock(spec=Logger)
        db_session = MagicMock(spec=DBSession)
        self.session.get_user_database_session = MagicMock(return_value=db_session)
        session_id = base_session_manager.add_session(self.session)


        with patch.object(self.session, 'dump_user_active_requests') as mock_dump, \
                patch.object(db_session, 'close') as mock_close:
            # Act
            base_session_manager.remove_session(session_id, app, logger)

            # Assert
            mock_dump.assert_called_once_with(app, logger, False, False)
            mock_close.assert_called_once()

        # Assert
        assert len(base_session_manager.get_sessions()) == 0
        assert len(base_session_manager.get_user_to_session()) == 0
        assert all([base_session_manager.get_timers()[timer_id] == [] for timer_id in base_session_manager.get_timers().keys()])


    def test_adding_session_to_session_manager_and_updating_session_expiration(self, base_session_manager, base_session):
        # Arrange
        session_id = base_session_manager.add_session(self.session)
        old_expiration = self.session.get_expiration_timestamp()
        for _ in range(10):
            base_session_manager.goto_next_timeslot()

        # Act
        base_session_manager.update_session_timer(session_id)

        # Assert
        assert self.session.get_expiration_timestamp() > old_expiration

def test_delete_expired_sessions():
    # Arrange
    session_manager = SessionManager(default_session_duration=5)  # 1 second for quick expiration
    db_session_1 = MagicMock(spec=DBSession)
    db_session_2 = MagicMock(spec=DBSession)
    session1 = Session(user_id="user1", project_primary_language=LanguageType("python"))
    session1.get_user_database_session = MagicMock(return_value=db_session_1)
    session2 = Session(user_id="user2", project_primary_language=LanguageType("python"))
    session2.get_user_database_session = MagicMock(return_value=db_session_2)

    session_id1 = session_manager.add_session(session1)
    session_id2 = session_manager.add_session(session2)

    session_manager.remove_session = MagicMock()

    stop_event = threading.Event()

    # Act
    def run_delete_expired_sessions():
        with patch('time.sleep', return_value=None):
            delete_expired_sessions(session_manager, stop_event)

    delete_thread = threading.Thread(target=run_delete_expired_sessions)
    delete_thread.start()

    # Wait for the sessions to expire
    time.sleep(secs=3)  # Wait enough time for sessions to expire and be deleted

    # Stop the thread after the test
    stop_event.set()
    delete_thread.join(timeout=1)


    # Assert
    # As the removal of the sessions is mocked, we can only check whether the function was called
    assert session_manager.remove_session.call_count == 2
    session_manager.remove_session.assert_any_call(session_id1, )
    session_manager.remove_session.assert_any_call(session_id2, )