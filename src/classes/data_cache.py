from loguru import logger
from pydantic import ValidationError

from src.classes.decorators import singleton
from src.models import Challenge, Product


@singleton
class DataCache:
    def __init__(self):
        self.stats: dict[int, dict[str, int | str]] = {}
        self.skills: dict[int, dict[int, str]] = {}
        self.courses: dict[int, dict[str, int | str]] = {}
        self.challenges: dict[str, Challenge] = {}
        self.products: dict[str, Product] = {}
        self.professions_info: dict[str, str] = {}
        self.skills_details: dict[int, dict[int, dict[str, str]]] = {}

    def update_stats(self, mock_data: list):
        headers = mock_data[0]
        self.stats = {
            int(row[0]): dict(zip(headers, [int(value) if value.isdigit() else value for value in row], strict=False))
            for row in mock_data[1:]
        }

    # DEPRECATED, changed to update_skills_details
    def update_skills(self, skills_data: list):
        for row in skills_data[1:]:
            self.skills.setdefault(int(row[1]), {})
            self.skills[int(row[1])].update({int(row[2]): row[3]})

    def update_skills_details(self, skills_details: list):
        for row in skills_details[1:]:
            if not row[0]:
                break

            if not row[0].isdigit() or not row[4].isdigit():
                continue

            program = int(row[0])
            lessons_completed = int(row[4])
            skill = row[5]
            skill_extended = row[6]

            self.skills_details.setdefault(program, {})[lessons_completed] = {
                "skill_short": skill,
                "skill_extended": skill_extended
            }

    def update_courses(self, courses_data: list):
        headers = courses_data[0]
        self.courses = {
            int(row[1]): dict(zip(headers, [int(value) if value.isdigit() else value for value in row], strict=False))
            for row in courses_data[1:]
        }

    def update_professions_info(self, professions_data: list):
        self.professions_info = {row[0]: row[3] for row in professions_data[1:]}

    def update_challenges(self, challenges_data: list):
        headers = challenges_data[0]
        self.challenges.clear()

        for row in challenges_data[1:]:
            try:
                challenge_dict = dict(
                    zip(headers, [int(value) if value.isdigit() else value for value in row], strict=False)
                )
                challenge = Challenge(**challenge_dict)
                self.challenges[challenge.id] = challenge
            except ValidationError as e:
                logger.error(f"Error while validating data for challenge {row[0]}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error while loading data for challenge {row[0]}: {e}")

        logger.info(f"Loaded {len(self.challenges)} challenges")

    def update_products(self, products_data: list):
        headers = products_data[0]
        self.products.clear()

        for row in products_data[1:]:
            try:
                product_dict = dict(
                    zip(headers, [int(value) if value.isdigit() else value for value in row], strict=False)
                )
                product = Product(**product_dict)
                self.products[product.id] = product
            except ValidationError as e:
                logger.error(f"Error while validating data for product {row[0]}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error while loading data for product {row[0]}: {e}")

        logger.info(f"Loaded {len(self.products)} products")
