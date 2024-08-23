from datetime import datetime

from fastapi import APIRouter, status, HTTPException, Depends, Security
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

SECRET_TOKEN = "ThisIsNotASecretToken146%"
api_key_header = APIKeyHeader(name="X-API-Key")


async def validate_token(key: str = Security(api_key_header)):
    if key != SECRET_TOKEN:
        print(f'api_key: {key}, SECRET_TOKEN: {SECRET_TOKEN}')
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate API key"
        )
    return None


api_router = APIRouter(dependencies=[Depends(validate_token)])


class Purchase(BaseModel):
    product_id: str
    student_id: int
    created_at: datetime = Field(default_factory=datetime.now)


@api_router.post("/bonuses/purchase")
async def purchase_product(data: Purchase):
    return JSONResponse(
        {
            "message": f"Product {data.product_id} purchased by student {data.student_id}",
            "status": "OK",
        },
        status_code=200
    )
