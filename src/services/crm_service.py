import aiohttp
from fastapi import HTTPException
from loguru import logger

from src.config import settings
from src.models import CRMSubmission


async def submit_phone_to_crm(data: CRMSubmission) -> str:
    url = settings.CRM_URL
    payload = {
        "phone": f"{data.phone}",
        "funnel": "direct",
        "sourceKey": "sharestats",
        "name": "Заявка на Карьерную Консультацию",
        "productId": 191,
        "utmTerm": f"referral-{data.student_id}",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Failed to submit phone to CRM. Status: {response.status}")
                    raise HTTPException(status_code=response.status, detail="CRM request failed")
                result = await response.text()
                logger.info(f"Phone {data.phone}, ref to student {data.student_id}. Result: {result}")
                return result
    except aiohttp.ClientError as e:
        logger.error(f"Failed to submit phone to CRM. Error: {e}")
        raise HTTPException(status_code=503, detail="Service Unavailable") from e
    except Exception as e:
        logger.error(f"Unexpected error when submitting phone to CRM. Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error") from e
