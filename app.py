from fastapi import FastAPI
from rag.router import router
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# Register the router
app.include_router(router)

