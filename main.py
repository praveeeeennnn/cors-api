from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
import time
import uuid

app = FastAPI(title="CORS Aware Metrics API")

EMAIL = "23f2000083@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://dash-rnh108.example.com"

# ----------------------------
# STRICT CORS
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# ----------------------------
# Middleware
# ----------------------------
@app.middleware("http")
async def add_headers(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()

    response = await call_next(request)

    process_time = time.perf_counter() - start

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.6f}"

    return response


@app.get("/")
def home():
    return {
        "message": "CORS Metrics API Running"
    }


@app.get("/stats")
def stats(values: str = Query(...)):
    nums = [int(x.strip()) for x in values.split(",") if x.strip()]

    return {
        "email": EMAIL,
        "count": len(nums),
        "sum": sum(nums),
        "min": min(nums),
        "max": max(nums),
        "mean": sum(nums) / len(nums)
    }