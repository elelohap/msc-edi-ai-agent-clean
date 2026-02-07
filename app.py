from fastapi import FastAPI
from rag.router import router
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
load_dotenv()

from fastapi.middleware.cors import CORSMiddleware



# app = FastAPI()


app = FastAPI(
    swagger_ui_parameters={
        "tryItOutEnabled": True,
        # optional but nice:
        "persistAuthorization": True,
    }
)

ALLOWED_ORIGINS = [
    "https://elelohap.github.io",
    "https://your-edi-site-domain.com",
    "https://www.your-edi-site-domain.com",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

# Register the router
app.include_router(router)

@app.get("/")
def root():
    return {"status": "ok", "message": "Use POST /ask"}

@app.get("/health")
def health():
    return {"status": "ok"}
