import aiohttp
from fastapi import HTTPException
from loguru import logger


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
                        except Exception as e:
                            logger.error(f"Response is not JSON: {e}")
                    elif response.status == 503:
                        raise HTTPException(status_code=503)
                    return {}

        except Exception as e:
            logger.error(f"Error while getting stats {student_id}: {e}")
            return {}
