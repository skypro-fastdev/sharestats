from src.classes.decorators import singleton


@singleton
class DataCache:
    def __init__(self):
        self.stats = {}
        self.skills = {}
        self.courses = {}

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
