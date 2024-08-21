from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from loguru import logger
from starlette.exceptions import HTTPException

from src.bot.client import bot
from src.config import settings, setup_middlewares
from src.dependencies import load_cache
from src.web.routes import router


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # Load mock data from Google Sheet
    load_cache()
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot has been started.")

    # Start periodic task for updating challenges
    # task = asyncio.create_task(update_challenges_periodically(cafeteria_loader, data_cache))

    yield

    # task.cancel()
    # try:
    #     await task
    # except asyncio.CancelledError:
    #     logger.info("Background task for updating challenges was cancelled")

    await bot.session.close()
    logger.info("Bot has been stopped.")


app = FastAPI(debug=settings.debug, lifespan=_lifespan)
setup_middlewares(app)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/data", StaticFiles(directory="data"), name="data")

app.include_router(router, prefix="/share")


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
            "message": "Мы проводим технические работы. Пожалуйста, попробуйте позже.",
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
