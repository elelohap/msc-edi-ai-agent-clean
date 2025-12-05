from fastapi import FastAPI
from rag.router import router
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Register the router
app.include_router(router)

# Mount static file server
app.mount("/", StaticFiles(directory=".", html=True), name="static")