from fastapi import HTTPException

from src.db.challenges_crud import ChallengeDBHandler
from src.db.students_crud import StudentDBHandler
from src.web.handlers import StudentHandler


async def get_or_create_student(
    student_id: int, handler: StudentHandler, students_crud: StudentDBHandler, challenges_crud: ChallengeDBHandler
) -> tuple:
    student = await students_crud.get_student_with_challenges(student_id)

    if not student:
        if not handler.student:
            raise HTTPException(status_code=404, detail="Страница не найдена")

        student = await students_crud.create_student(handler.student)
        if not student:
            raise HTTPException(status_code=500, detail="Failed to create a new student in DB")

        # Calculate challenges and add points
        active_challenges, completed_challenges = await challenges_crud.update_new_student_challenges(student)
        # Refresh student data
        student = await students_crud.get_student(student_id)

        if not student:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated student data")
    else:
        completed_challenges = [c.challenge for c in student.student_challenges]
        active_challenges = await challenges_crud.get_all_challenges(
            active_only=True, profession=student.profession.name
        )

    return student, active_challenges, completed_challenges
