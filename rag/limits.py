# rag/limits.py
from fastapi import Request
from slowapi import Limiter

def real_ip(request: Request) -> str:
    # Render/proxies
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

limiter = Limiter(key_func=real_ip)
