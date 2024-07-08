import threading
import time

from Types import LanguageType, IDEType

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
    def __base_settings(self):
        return {
            "store_completions": False,
            "store_context": False,
            "ask_for_feedback": True,
        }


class Session:
    def __init__(self, user_id: str, project_primary_language: LanguageType = None,
                 project_ide: IDEType = None, user_settings: dict = None):
        """
        Initialize a new session.
        """
        self.__user_id = user_id
        self.__project_primary_language = project_primary_language
        self.__project_ide = project_ide
        self.__user_settings = UserSetting(user_settings)
        self.__expiration_timestamp = None

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


class SessionManager:
    def __init__(self, default_session_duration: int = 3600):
        """
        Initialize a new session manager.
        """
        self.__sessions = {}
        self.__current_timeslot = 0
        self.__timers = {} # this will be a dict with the key being the timeslot and the value being a list of session ids
        self.__default_session_duration = default_session_duration

        # implement a multithreaded operation occupying one thread for the entire session manager that will
        # remove a session from the session manager if the session has expired
        def delete_expired_sessions(self):
            while True:
                if self.__current_timeslot in self.__timers:
                    for session_id in self.__timers[self.__current_timeslot]:
                        session = self.__sessions[session_id]
                        if session.get_expiration_timestamp() <= self.__current_timeslot:
                            del self.__sessions[session_id]
                            self.__timers[self.__current_timeslot].remove(session_id)
                self.__current_timeslot += 1
                time.sleep(5)

        threading.Thread(target=delete_expired_sessions(self)).start()

    def add_session(self, session: Session):
        """
        Add a new session to the session manager.
        """
        session.set_expiration_timestamp(self.__current_timeslot + self.__default_session_duration)
        session_id = str(hash(session))
        self.__sessions[session_id] = session
        if session.get_expiration_timestamp() not in self.__timers:
            self.__timers[session.get_expiration_timestamp()] = []
        self.__timers[session.get_expiration_timestamp()].append(session_id)
        return session_id

    def get_session(self, session_id: str) -> Session | None:
        """
        Get a session from the session manager.
        """
        return self.__sessions.get(session_id)

    def remove_session(self, session_id: str):
        """
        Remove a session from the session manager.
        """
        session = self.__sessions[session_id]
        del self.__sessions[session_id]
        self.__timers[session.get_expiration_timestamp()].remove(session_id)

    def update_session_timer(self, session_id: str):
        """
        Update the expiration timestamp for a session.
        """
        session = self.__sessions[session_id]
        new_expiration_timestamp = self.__current_timeslot + self.__default_session_duration
        self.__timers[session.get_expiration_timestamp()].remove(session_id)
        session.set_expiration_timestamp(new_expiration_timestamp)
        if session.get_expiration_timestamp() not in self.__timers:
            self.__timers[session.get_expiration_timestamp()] = []
        self.__timers[session.get_expiration_timestamp()].append(session_id)