from json import JSONDecodeError

import aiohttp
from fastapi import HTTPException

from src.bot.logger import tg_logger


class StatsLoader:
    def __init__(self, url: str, token: str):
        self.__url = url
        self.__token = token

    async def get_stats(self, student_id: int) -> dict[str, int | str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.__url, params={"student_id": student_id}, headers={"X-Authorization-Token": self.__token}
                ) as response:
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
                "ERROR",
                f"Unexpected error in while getting stats from Yandex API for student_id {student_id}\n{e}",
            )
            return {}
