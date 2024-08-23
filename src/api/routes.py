from fastapi import APIRouter, status, Depends, Security
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader

from src.models import Purchase

SECRET_TOKEN = "ThisIsNotASecretToken146%"  # JUST FOR TESTS
api_key_header = APIKeyHeader(name="X-API-Key")


async def validate_token(key: str = Security(api_key_header)):
    if key != SECRET_TOKEN:
        return JSONResponse({"message": "Invalid API key"}, status_code=status.HTTP_403_FORBIDDEN)
    return None


api_router = APIRouter(dependencies=[Depends(validate_token)])


@api_router.post("/bonuses/purchase")
async def purchase_product(data: Purchase):
    return JSONResponse(
        {
            "message": f"Product {data.product_id} purchased by student {data.student_id}",
            "status": "OK",
        },
        status_code=status.HTTP_200_OK
    )
