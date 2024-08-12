import datetime
import threading
import time
from logging import Logger

import sqlalchemy.orm
from fastapi import FastAPI

from database.app_to_db import add_active_request_to_db
from models import GenerateRequest, VerifyRequest
from models.Types import LanguageType, IDEType
from models.Lifecycle import ActiveRequest


class UserSetting:
    """
    User settings stored on the user's device
    """

    def __init__(self, settings: dict):
        self.__settings = settings
        if self.__settings is None:
            self.__settings = {}
        for key in self.__settings.keys():
            if isinstance(self.__settings[key], str):
                if self.__settings[key].lower() == "true":
                    self.__settings[key] = True
                elif self.__settings[key].lower() == "false":
                    self.__settings[key] = False

        base_settings = self.__base_settings()
        for key in base_settings.keys():
            if key not in self.__settings.keys():
                self.__settings[key] = self.__base_settings()[key]
            else:
                assert isinstance(
                    self.__settings[key], type(base_settings[key])
                ), f"Expected instance of {base_settings[key]} for key {key}, got {self.__settings[key]}"

    def __getitem__(self, key):
        return self.__settings[key]

    def __setitem__(self, key, value):
        self.__settings[key] = value

    def __delitem__(self, key):
        del self.__settings[key]

    # define behavior for when the .keys() method is called
    def keys(self):
        return self.__settings.keys()

    @staticmethod
    def __base_settings():
        return {
            "store_completions": False,
            "store_context": False,
            "ask_for_feedback": True,
        }


class Session:
    def __init__(
        self,
        user_id: str,
        project_primary_language: LanguageType = None,
        project_ide: IDEType = None,
        user_settings: dict = None,
        db_session: sqlalchemy.orm.Session = None,
        project_coco_version: str = None,
    ):
        """
        Initialize a new session.
        """
        self.__user_id = user_id
        self.__project_primary_language = project_primary_language
        self.__project_ide = project_ide
        self.__coco_version = project_coco_version
        self.__user_settings = UserSetting(user_settings)
        self.__session_since = datetime.datetime.now()
        self.__expiration_timestamp = None
        self.__user_database_session = db_session
        self.__user_active_requests = {}
        self.__user_request_count = 0

    def add_active_request(
        self,
        request_id: str,
        request: GenerateRequest,
        completions: dict,
        time_taken: float,
    ):
        self.__user_active_requests[request_id] = ActiveRequest.model_validate(
            {
                "request": request,
                "completions": {
                    key: {
                        "completion": completions[key],
                        "shown_at": [],
                        "accepted": False,
                    }
                    for key in completions.keys()
                },
                "time_taken": round(time_taken * 1000),  # convert to round milliseconds
                "ground_truth": [],
            }
        )
        self.increment_user_request_count()

    def get_session_since(self) -> datetime.datetime:
        return self.__session_since

    def get_active_request(self, request_id: str) -> ActiveRequest:
        return self.__user_active_requests[request_id]

    def update_active_request(self, request_id: str, verify_req: VerifyRequest) -> bool:
        try:
            # update whether a given model was chosen
            if verify_req.chosen_model is not None and len(verify_req.chosen_model) > 0:
                self.__user_active_requests[request_id].completions[
                    verify_req.chosen_model
                ]["accepted"] = True

            # update the times at which the completions were shown
            if verify_req.shown_at is not None:
                for key in verify_req.shown_at.keys():
                    for item in verify_req.shown_at[key]:
                        if (
                            item
                            not in self.__user_active_requests[request_id].completions[
                                key
                            ]["shown_at"]
                        ):
                            self.__user_active_requests[request_id].completions[key][
                                "shown_at"
                            ].append(item)

            # update the ground truth completions
            if verify_req.ground_truth is not None:
                for val in verify_req.ground_truth:
                    if val not in self.__user_active_requests[request_id].ground_truth:
                        self.__user_active_requests[request_id].ground_truth.append(val)
        except Exception:
            return False
        return True

    def dump_user_active_requests(
        self, app: FastAPI, logger: Logger, store_completions: bool, store_context: bool
    ) -> None:
        """
        A function to dump the active requests of a user to the database.
        """
        for request_id in self.__user_active_requests.keys():
            request = self.__user_active_requests[request_id]
            try:
                add_active_request_to_db(
                    self.__user_database_session,
                    request,
                    self.__user_id,
                    self.__coco_version,
                    app,
                    logger,
                    store_completions,
                    store_context,
                )
            except Exception as e:
                logger.error(
                    f"Error while dumping active request {request_id} to the database: {e}"
                )
                continue

    def get_user_id(self) -> str:
        return self.__user_id

    def get_coco_version(self) -> str:
        return self.__coco_version

    def get_project_primary_language(self) -> LanguageType | None:
        return self.__project_primary_language

    def get_project_ide(self) -> IDEType | None:
        return self.__project_ide

    def get_user_settings(self) -> UserSetting:
        return self.__user_settings

    def get_expiration_timestamp(self) -> int:
        return self.__expiration_timestamp

    def set_expiration_timestamp(self, expiration_timestamp: int):
        self.__expiration_timestamp = expiration_timestamp

    def get_user_active_requests(self) -> dict:
        return self.__user_active_requests

    def add_user_active_request(self, request_id: str, request: dict):
        self.__user_active_requests[request_id] = request

    def increment_user_request_count(self):
        self.__user_request_count += 1

    def get_user_request_count(self) -> int:
        return self.__user_request_count

    def remove_user_active_request(self, request_id: str):
        del self.__user_active_requests[request_id]

    def get_user_database_session(self) -> sqlalchemy.orm.Session:
        return self.__user_database_session


class SessionManager:
    def __init__(self, default_session_duration: int = 3600):
        """
        Initialize a new session manager.
        """
        self.__sessions = {}
        self.__current_timeslot = 0
        self.__timers = (
            {}
        )  # this will be a dict with the key being the timeslot and the value being a list of session ids
        self.__default_session_duration = default_session_duration
        self.__user_to_session = {}
        self.__lock = threading.Lock()

        # implement a multithreaded operation occupying one thread for the entire session manager that will
        # remove a session from the session manager if the session has expired

    def get_current_timeslot(self) -> int:
        with self.__lock:
            return self.__current_timeslot

    def goto_next_timeslot(self):
        with self.__lock:
            self.__current_timeslot += 1

    def get_timers(self) -> dict:
        with self.__lock:
            return self.__timers

    def get_sessions(self) -> dict:
        with self.__lock:
            return self.__sessions

    def get_session_id_by_user_token(self, user_token: str) -> str | None:
        with self.__lock:
            return self.__user_to_session.get(user_token)

    def get_user_to_session(self) -> dict:
        with self.__lock:
            return self.__user_to_session

    def add_session(self, session: Session) -> str:
        """
        Add a new session to the session manager.
        """
        session.set_expiration_timestamp(
            self.__current_timeslot + (self.__default_session_duration // 5)
        )
        session_id = str(hash(session))
        with self.__lock:
            self.__sessions[session_id] = session
            if session.get_expiration_timestamp() not in self.__timers:
                self.__timers[session.get_expiration_timestamp()] = []
            self.__timers[session.get_expiration_timestamp()].append(session_id)
            self.__user_to_session[session.get_user_id()] = session_id
            return session_id

    def get_session(self, session_id: str) -> Session | None:
        """
        Get a session from the session manager.
        """
        with self.__lock:
            return self.__sessions.get(session_id)

    def remove_session(self, session_id: str, app: FastAPI, logger: Logger):
        """
        Remove a session from the session manager.
        """
        with self.__lock:
            session = self.__sessions[session_id]
            session_user_settings = session.get_user_settings()
            session.dump_user_active_requests(
                app,
                logger,
                session_user_settings["store_completions"],
                session_user_settings["store_context"],
            )
            session.get_user_database_session().close()  # close the database session so there are no memory leaks
            del self.__user_to_session[session.get_user_id()]
            del self.__sessions[session_id]
            self.__timers[session.get_expiration_timestamp()].remove(session_id)

    def update_session_timer(self, session_id: str):
        """
        Update the expiration timestamp for a session.
        """
        with self.__lock:
            session = self.__sessions[session_id]
            new_expiration_timestamp = self.__current_timeslot + (
                self.__default_session_duration // 5
            )
            self.__timers[session.get_expiration_timestamp()].remove(session_id)
            session.set_expiration_timestamp(new_expiration_timestamp)
            if session.get_expiration_timestamp() not in self.__timers:
                self.__timers[session.get_expiration_timestamp()] = []
            self.__timers[session.get_expiration_timestamp()].append(session_id)


def delete_expired_sessions(
    session_manager: SessionManager, stop_event: threading.Event = None
):
    while not stop_event.is_set():
        if session_manager.get_current_timeslot() in session_manager.get_timers():
            timers = session_manager.get_timers()
            for session_id in timers[session_manager.get_current_timeslot()]:
                session = session_manager.get_sessions()[session_id]
                if (
                    session.get_expiration_timestamp()
                    <= session_manager.get_current_timeslot()
                ):
                    session_manager.remove_session(session_id)
        session_manager.goto_next_timeslot()
        time.sleep(5)
