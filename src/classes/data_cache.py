from loguru import logger
from pydantic import ValidationError

from src.classes.decorators import singleton
from src.models import Challenge, Meme, Product


@singleton
class DataCache:
    def __init__(self):
        self.stats: dict[int, dict[str, int | str]] = {}
        self.courses: dict[int, dict[str, int | str]] = {}
        self.meme_data: dict[str, Meme] = {}
        self.professions_info: dict[str, str] = {}
        self.skills_details: dict[int, dict[int, dict[str, str]]] = {}
        self.skills: dict[int, dict[int, str]] = {}  # DEPRECATED
        self.challenges: dict[str, Challenge] = {}  # DEPRECATED
        self.products: dict[str, Product] = {}  # DEPRECATED

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
                "skill_extended": skill_extended,
            }

    def update_courses(self, courses_data: list):
        headers = courses_data[0]
        self.courses = {
            int(row[1]): dict(zip(headers, [int(value) if value.isdigit() else value for value in row], strict=False))
            for row in courses_data[1:]
        }

    def update_professions_info(self, professions_data: list):
        self.professions_info = {row[0]: row[3] for row in professions_data[1:]}

    # DEPRECATED
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

    # DEPRECATED
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

    def update_meme_data(self, meme_data: list):
        headers = meme_data[0]
        self.meme_data.clear()

        for row in meme_data[1:]:
            try:
                meme_dict = dict(zip(headers, [value.strip() for value in row], strict=False))
                meme = Meme(**meme_dict)
                self.meme_data[meme.id] = meme
            except ValidationError as e:
                logger.error(f"Error while validating data for meme {row[0]}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error while loading data for meme {row[0]}: {e}")

        logger.info(f"Loaded {len(self.meme_data)} memes")
