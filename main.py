from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from collections import deque
import time
import uuid
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import jwt

app = FastAPI()

EMAIL = "23f2000083@ds.study.iitm.ac.in"

# -----------------------------
# STRICT CORS (ONLY allowed origin)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dash-rnh108.example.com"
    ],
    allow_credentials=False,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

# -----------------------------
# Startup time
# -----------------------------
START_TIME = time.time()

# -----------------------------
# Prometheus metrics
# -----------------------------
REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests"
)

# -----------------------------
# Store last 500 logs
# -----------------------------
LOGS = deque(maxlen=500)


# -----------------------------
# Middleware
# -----------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):

    REQUEST_COUNTER.inc()

    request_id = str(uuid.uuid4())

    start = time.perf_counter()

    response = await call_next(request)

    process_time = time.perf_counter() - start

    LOGS.append({
        "level": "INFO",
        "ts": time.time(),
        "path": request.url.path,
        "request_id": request_id
    })

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.6f}"

    return response


# -----------------------------
# Home
# -----------------------------
@app.get("/")
def home():
    return {
        "message": "Production Observability API Running"
    }


# -----------------------------
# REQUIRED BY QUESTION 1
# GET /stats?values=1,2,3
# -----------------------------
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


# -----------------------------
# Work endpoint
# -----------------------------
@app.get("/work")
def work(n: int = 1):

    for _ in range(n):
        pass

    return {
        "email": EMAIL,
        "done": n
    }


# -----------------------------
# Prometheus metrics
# -----------------------------
@app.get("/metrics")
def metrics():

    return PlainTextResponse(
        generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST
    )


# -----------------------------
# Health
# -----------------------------
@app.get("/healthz")
def healthz():

    return {
        "status": "ok",
        "uptime_s": time.time() - START_TIME
    }


# -----------------------------
# Tail logs
# -----------------------------
@app.get("/logs/tail")
def logs_tail(limit: int = 10):

    return list(LOGS)[-limit:]

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-f1cwzwuq.apps.exam.local"


class VerifyRequest(BaseModel):
    token: str

@app.post("/verify")
def verify(req: VerifyRequest):
    try:
        payload = jwt.decode(
            req.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
        )

        return {
            "valid": True,
            "email": payload.get("email"),
            "sub": payload.get("sub"),
            "aud": payload.get("aud"),
        }

    except jwt.PyJWTError:
        return JSONResponse(
            status_code=401,
            content={"valid": False},
        )