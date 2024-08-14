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
    load_cache()
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot has been started.")
    yield
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

    if exc.status_code == 404:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    if exc.status_code == 500:
        return templates.TemplateResponse("500.html", {"request": request}, status_code=500)
    if exc.status_code == 503:
        return templates.TemplateResponse("503.html", {"request": request}, status_code=503)
    return None


if __name__ == "__main__":
    import uvicorn

    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Application has been stopped.")
