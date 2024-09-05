import csv
from io import StringIO
from typing import Sequence

from sqlalchemy import Row


def generate_csv(students: Sequence[Row]) -> StringIO:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["student_id", "last_login"])

    if not students:
        return buffer

    for student in students:
        writer.writerow([student.id, student.last_login])

    return buffer
