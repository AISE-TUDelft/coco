import threading
import time

import sqlalchemy.orm

from models.Types import LanguageType, IDEType

class UserSetting:
    """
    User settings stored on the user's device
    """

    def __init__(self, settings: dict):
        self.__settings = settings
        base_settings = self.__base_settings()
        for key in base_settings.keys():
            if key not in self.__settings:
                self.__settings[key] = self.__base_settings()[key]
            else:
                assert type(self.__settings[key]) == type(base_settings[key]), \
                    f"Expected type {type(base_settings[key])} for key {key}, got {type(self.__settings[key])}"

    @staticmethod
    def __base_settings():
        return {
            "store_completions": False,
            "store_context": False,
            "ask_for_feedback": True,
        }


class Session:
    def __init__(self, user_id: str, project_primary_language: LanguageType = None,
                 project_ide: IDEType = None, user_settings: dict = None, db_session: sqlalchemy.orm.Session = None):
        """
        Initialize a new session.
        """
        self.__user_id = user_id
        self.__project_primary_language = project_primary_language
        self.__project_ide = project_ide
        self.__user_settings = UserSetting(user_settings)
        self.__expiration_timestamp = None
        self.__user_database_session = db_session
        self.__user_active_requests = {}
        self.__user_request_count = 0

    def get_user_id(self) -> str:
        return self.__user_id

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
        self.__timers = {} # this will be a dict with the key being the timeslot and the value being a list of session ids
        self.__default_session_duration = default_session_duration
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


    def add_session(self, session: Session):
        """
        Add a new session to the session manager.
        """
        session.set_expiration_timestamp(self.__current_timeslot + (self.__default_session_duration // 5))
        session_id = str(hash(session))
        with self.__lock:
            self.__sessions[session_id] = session
            if session.get_expiration_timestamp() not in self.__timers:
                self.__timers[session.get_expiration_timestamp()] = []
            self.__timers[session.get_expiration_timestamp()].append(session_id)
            return session_id

    def get_session(self, session_id: str) -> Session | None:
        """
        Get a session from the session manager.
        """
        with self.__lock:
            return self.__sessions.get(session_id)

    def remove_session(self, session_id: str):
        """
        Remove a session from the session manager.
        """
        with self.__lock:
            session = self.__sessions[session_id]
            session.get_user_database_session().close() # close the database session so there are no memory leaks
            del self.__sessions[session_id]
            self.__timers[session.get_expiration_timestamp()].remove(session_id)

    def update_session_timer(self, session_id: str):
        """
        Update the expiration timestamp for a session.
        """
        with self.__lock:
            session = self.__sessions[session_id]
            new_expiration_timestamp = self.__current_timeslot + (self.__default_session_duration // 5)
            self.__timers[session.get_expiration_timestamp()].remove(session_id)
            session.set_expiration_timestamp(new_expiration_timestamp)
            if session.get_expiration_timestamp() not in self.__timers:
                self.__timers[session.get_expiration_timestamp()] = []
            self.__timers[session.get_expiration_timestamp()].append(session_id)


def delete_expired_sessions(session_manager: SessionManager):
    while True:
        if session_manager.get_current_timeslot() in session_manager.get_timers():
            timers = session_manager.get_timers()
            for session_id in timers[session_manager.get_current_timeslot()]:
                session = session_manager.get_sessions()[session_id]
                if session.get_expiration_timestamp() <= session_manager.get_current_timeslot():
                    session.get_user_database_session().close()  # close the database session so there are no memory leaks
                    del session_manager.get_sessions()[session_id]
                    session_manager.get_timers()[session_manager.get_current_timeslot()].remove(session_id)
        session_manager.goto_next_timeslot()
        time.sleep(5)