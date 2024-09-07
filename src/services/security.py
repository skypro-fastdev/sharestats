import hashlib

from fastapi import HTTPException

from src.bot.logger import tg_logger
from src.config import settings


def verify_hash(student_id, expected_hash):
    combined = f"{student_id}{settings.SALT}".encode("utf-8")
    sha256 = hashlib.sha256()
    sha256.update(combined)
    calculated_hash = sha256.hexdigest()[:8]

    return calculated_hash == expected_hash


async def verify_hash_dependency(student_id: int, hash: str | None = None) -> None:  # noqa: A002
    if not verify_hash(student_id, hash):
        await tg_logger.log("ERROR", f"Invalid hash for student {student_id}: {hash}")
        raise HTTPException(status_code=404, detail="Страница не найдена")
