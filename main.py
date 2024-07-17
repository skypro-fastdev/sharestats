from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.config import setup_cors
from src.web.routes import router

app = FastAPI()

setup_cors(app)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/data", StaticFiles(directory="data"), name="data")

app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
