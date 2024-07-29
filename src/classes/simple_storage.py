from src.classes.decorators import singleton
from src.models import Achievement
from src.web.handlers import StudentHandler


@singleton
class SimpleStorage:
    def __init__(self):
        self.__storage: dict[int, dict[str, Achievement | StudentHandler]] = {}

    def set(self, student_id: int, achievement: Achievement, handler: StudentHandler):
        self.__storage[student_id] = {"achievement": achievement, "handler": handler}

    def get(self, student_id: int):
        return self.__storage.get(student_id)

    def pop(self, student_id: int):
        return self.__storage.pop(student_id, None)
