import csv
from io import StringIO
from typing import Sequence

from sqlalchemy import Row

from src.db.models import StudentProduct


def generate_csv(data: Sequence[Row] | list[StudentProduct], type_: str) -> StringIO:
    buffer = StringIO()
    writer = csv.writer(buffer)

    if not data:
        return buffer

    match type_:
        case "last_login":
            writer.writerow(["student_id", "last_login"])
            for student in data:
                writer.writerow([student.id, student.last_login])
        case "adoption":
            writer.writerow(
                [
                    "student_id",
                    "bonuses_last_visited",
                    "completed_challenges",
                    "purchased_products",
                ]
            )
            for student in data:
                writer.writerow(
                    [student.id, student.bonuses_last_visited, student.completed_challenges, student.purchased_products]
                )
        case "purchases":
            writer.writerow(["student_id", "product_id", "created_at", "added_by"])
            for purchase in data:
                writer.writerow([purchase.student_id, purchase.product_id, purchase.created_at, purchase.added_by])

    return buffer
