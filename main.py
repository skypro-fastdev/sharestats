import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.exceptions import HTTPException

from src.api.routes import api_router, open_api_router
from src.bot.client import bot
from src.config import settings, setup_middlewares
from src.dependencies import data_cache, load_cache, mock_data_loader
from src.services.background_tasks import update_meme_data_periodically
from src.web.badges import router as badges_router

# from src.web.bonuses import router as bonuses_router
from src.web.sharestats import router as sharestats_router


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # Load mock data from Google Sheet
    load_cache()
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot has been started.")

    # Start periodic task for updating memes
    update_memes_task = asyncio.create_task(update_meme_data_periodically(mock_data_loader, data_cache))

    yield

    update_memes_task.cancel()
    try:
        await update_memes_task
    except asyncio.CancelledError:
        logger.info("Background task for updating memes was cancelled")

    await bot.session.close()
    logger.info("Bot has been stopped.")


app = FastAPI(debug=settings.debug, lifespan=_lifespan)
setup_middlewares(app)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/data", StaticFiles(directory="data"), name="data")

app.include_router(sharestats_router, prefix="/share", include_in_schema=False)
# app.include_router(bonuses_router, prefix="/share", include_in_schema=False)

app.include_router(badges_router, prefix="/share", include_in_schema=False)
app.include_router(api_router, prefix="/share", include_in_schema=True)
app.include_router(open_api_router, prefix="/share", include_in_schema=True)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    from fastapi.templating import Jinja2Templates

    templates = Jinja2Templates(directory="src/templates")

    status_code = str(exc.status_code)

    error_details = {
        "404": {"title": "Здесь ничего нет", "message": "Попробуй перейти по прямой ссылке из личного кабинета"},
        "500": {
            "title": "Внутренняя ошибка сервера",
            "message": "Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже.",
        },
        "503": {
            "title": "Сервис временно недоступен",
            "message": "Пожалуйста, попробуйте зайти позже.",
        },
        "504": {
            "title": "Сервис временно недоступен",
            "message": "Пожалуйста, попробуйте зайти через 5 минут.",
        },
    }

    details = error_details.get(
        status_code,
        {
            "title": "Произошла ошибка",
            "message": exc.detail if exc.detail else "Пожалуйста, попробуйте еще раз или обратитесь в поддержку.",
        },
    )

    return templates.TemplateResponse(
        "error.html",
        {"request": request, "status_code": status_code, "title": details["title"], "message": details["message"]},
        status_code=exc.status_code,
    )


if __name__ == "__main__":
    import uvicorn

    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Application has been stopped.")
