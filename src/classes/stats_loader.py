import asyncio.exceptions
from json import JSONDecodeError

import aiohttp
from fastapi import HTTPException
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.bot.logger import tg_logger


class StatsLoader:
    def __init__(self, url: str, token: str):
        self.__url = url
        self.__token = token

    @retry(
        stop=stop_after_attempt(5),  # Максимум 5 попыток
        wait=wait_exponential(multiplier=1, min=5, max=10),  # Ждём от 1 до 10 секунд между попытками
        retry=retry_if_exception_type(asyncio.exceptions.TimeoutError),  # Повторяем только при таймаутах
    )
    async def get_stats(self, student_id: int) -> dict[str, int | str]:
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            params = {"student_id": student_id}
            headers = {"X-Authorization-Token": self.__token}

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.__url, params=params, headers=headers) as response:
                    if response.status == 200:
                        try:
                            return await response.json()
                        except JSONDecodeError as e:
                            await tg_logger.log(
                                "ERROR",
                                f"Failed to decode JSON response for student_id {student_id}: {e}",
                            )
                    else:
                        await tg_logger.log(
                            "WARNING",
                            f"Unexpected response from Yandex API for student_id: {student_id}\n"
                            f"Status: {response.status}\n"
                            f"Reason: {response.reason}",
                        )
                        raise HTTPException(status_code=response.status, detail=response.reason)
                    return {}
        except aiohttp.ClientError as e:
            await tg_logger.log(
                "ERROR",
                f"Network error while getting stats for student_id {student_id}: {e}",
            )
            return {}
        except Exception as e:
            await tg_logger.log(
                "ERROR", f"Unexpected error while getting stats from Yandex API for student_id {student_id}\n{e}"
            )
            return {}
