from abc import ABC, abstractmethod

class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    def run(self, session_id: str, user_input: str):
        raise NotImplementedError

    @abstractmethod
    def stream(self, session_id: str, user_input: str):
        raise NotImplementedError
