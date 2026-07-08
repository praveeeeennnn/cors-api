from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

app = FastAPI(title="Q1 CORS Metrics API")

EMAIL = "23f2000083@ds.study.iitm.ac.in"
ALLOWED_ORIGIN = "https://dash-rnh108.example.com"

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)

# Required Middleware Headers
@app.middleware("http")
async def add_headers(request: Request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.6f}"

    return response


@app.get("/")
def home():
    return {"message": "Q1 Metrics API Running"}


@app.get("/stats")
def stats(values: str = Query(...)):
    numbers = [int(x.strip()) for x in values.split(",") if x.strip()]

    return {
        "email": EMAIL,
        "count": len(numbers),
        "sum": sum(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "mean": sum(numbers) / len(numbers),
    }