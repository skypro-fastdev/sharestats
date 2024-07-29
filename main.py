from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from loguru import logger

from src.bot.client import bot
from src.config import IS_HEROKU, settings, setup_middlewares
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

if IS_HEROKU:
    app.include_router(router, prefix="/share")
else:
    app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    try:
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Application has been stopped.")
