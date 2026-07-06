import time
import uuid
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

EMAIL = "23f2000083@ds.study.iitm.ac.in"
ALLOWED_ORIGIN = "https://dash-rnh108.example.com"

app = FastAPI()

# Allow only the assigned origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# Middleware to add required headers
class HeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()

        response = await call_next(request)

        process_time = time.perf_counter() - start

        response.headers["X-Request-ID"] = str(uuid.uuid4())
        response.headers["X-Process-Time"] = f"{process_time:.6f}"

        return response

app.add_middleware(HeaderMiddleware)

@app.get("/")
def home():
    return {"message": "CORS Metrics API is running"}

@app.get("/stats")
def stats(values: str = Query(...)):
    numbers = [int(x.strip()) for x in values.split(",") if x.strip()]

    count = len(numbers)
    total = sum(numbers)

    return {
        "email": EMAIL,
        "count": count,
        "sum": total,
        "min": min(numbers),
        "max": max(numbers),
        "mean": total / count
    }