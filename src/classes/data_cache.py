from src.classes.decorators import singleton
from src.models import Challenge


@singleton
class DataCache:
    def __init__(self):
        self.stats: dict[int, dict[str, int | str]] = {}
        self.skills: dict[int, dict[int, str]] = {}
        self.courses: dict[int, dict[str, int | str]] = {}
        self.challenges: dict[str, Challenge] = {}

    def update_stats(self, mock_data: list):
        headers = mock_data[0]
        self.stats = {
            int(row[0]): dict(zip(headers, [int(value) if value.isdigit() else value for value in row], strict=False))
            for row in mock_data[1:]
        }

    def update_skills(self, skills_data: list):
        for row in skills_data[1:]:
            self.skills.setdefault(int(row[1]), {})
            self.skills[int(row[1])].update({int(row[2]): row[3]})

    def update_courses(self, courses_data: list):
        headers = courses_data[0]
        self.courses = {
            int(row[1]): dict(zip(headers, [int(value) if value.isdigit() else value for value in row], strict=False))
            for row in courses_data[1:]
        }

    def update_challenges(self, challenges_data: list):
        headers = challenges_data[0]

        self.challenges = {
            row[0]: Challenge(
                **dict(zip(headers, [int(value) if value.isdigit() else value for value in row], strict=False))
            )
            for row in challenges_data[1:]
        }
