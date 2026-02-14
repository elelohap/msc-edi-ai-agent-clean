from fastapi import FastAPI
from fastapi import Request
from rag.router import router
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from fastapi.responses import JSONResponse

#from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from slowapi import _rate_limit_exceeded_handler


from rag.limits import limiter


load_dotenv()

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    swagger_ui_parameters={
        "tryItOutEnabled": True,
        # optional but nice:
        "persistAuthorization": True,
    }
)

# Use proxy-aware IP detection
def real_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


ALLOWED_ORIGINS = [
    "https://elelohap.github.io",
    "https://cde.nus.edu.sg",
    "https://www.your-edi-site-domain.com",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def real_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host

limiter = Limiter(key_func=real_ip)
app.state.limiter = limiter


# Register the router
app.include_router(router)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests. Please try again in a minute."},
    )


@app.get("/")
def root():
    return {"status": "ok", "message": "Use POST /ask"}

@app.get("/health")
def health():
    return {"status": "ok"}
