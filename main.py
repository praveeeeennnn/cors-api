from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from collections import deque
import time
import uuid

app = FastAPI()

EMAIL = "23f2000083@ds.study.iitm.ac.in"

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup time
START_TIME = time.time()

# Prometheus Counter
REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP requests"
)

# Store last 500 logs
LOGS = deque(maxlen=500)


# Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):

    REQUEST_COUNTER.inc()

    request_id = str(uuid.uuid4())

    response = await call_next(request)

    LOGS.append({
        "level": "INFO",
        "ts": time.time(),
        "path": request.url.path,
        "request_id": request_id
    })

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/")
def home():
    return {
        "message": "Production Observability API Running"
    }


@app.get("/work")
def work(n: int = 1):

    # Simulate K units of work
    for _ in range(n):
        pass

    return {
        "email": EMAIL,
        "done": n
    }


@app.get("/metrics")
def metrics():

    return PlainTextResponse(
        generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/healthz")
def healthz():

    return {
        "status": "ok",
        "uptime_s": time.time() - START_TIME
    }


@app.get("/logs/tail")
def logs_tail(limit: int = 10):

    return list(LOGS)[-limit:]