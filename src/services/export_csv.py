import csv
from io import StringIO
from typing import Sequence

from src.db.models import StudentDB


def generate_csv(students: Sequence[StudentDB]) -> StringIO:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["student_id", "last_login"])

    if not students:
        return buffer

    for student in students:
        writer.writerow([student.id, student.last_login])

    return buffer
