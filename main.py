from fastapi import FastAPI, Request, Query, Header
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from dotenv import load_dotenv
import jwt
import yaml
import os
import uuid
import time
import logging
from pathlib import Path

# ----------------------------
# Load Environment
# ----------------------------
load_dotenv()

EMAIL = "23f2000083@ds.study.iitm.ac.in"

ALLOWED_ORIGIN = "https://dash-rnh108.example.com"

ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-f1cwzwuq.apps.exam.local"

API_KEY = os.getenv("API_KEY", "secret123")

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4LlgniT7GlkL9Mce3b0wGLs9/7ZIXdQIDAQAB
-----END PUBLIC KEY-----"""

app = FastAPI(title="TDS Exam API")

# ----------------------------
# Strict CORS
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ----------------------------
# Logging
# ----------------------------
Path("logs").mkdir(exist_ok=True)

logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(__name__)

# ----------------------------
# Prometheus Counter
# ----------------------------
REQUEST_COUNTER = Counter(
    "http_requests_total",
    "Total HTTP Requests"
)

analytics_events = []

# ----------------------------
# Middleware
# ----------------------------
@app.middleware("http")
async def middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()

    REQUEST_COUNTER.inc()

    response = await call_next(request)

    duration = time.perf_counter() - start

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{duration:.6f}"

    logger.info(
        "%s %s %.6f",
        request.method,
        request.url.path,
        duration
    )

    return response

# ----------------------------
# Home
# ----------------------------
@app.get("/")
def home():
    return {
        "message": "TDS Exam API Running"
    }

# ==========================================================
# Models
# ==========================================================

class VerifyRequest(BaseModel):
    token: str


class AnalyticsEvent(BaseModel):
    event: str
    value: float


# ==========================================================
# Q1 : CORS Aware Metrics API
# ==========================================================

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


# ==========================================================
# Q2 : OAuth2 / OIDC Verify
# ==========================================================

@app.post("/verify")
def verify(request: VerifyRequest):

    try:

        payload = jwt.decode(
            request.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
        )

        return {
            "valid": True,
            "email": EMAIL,
            "sub": payload.get("sub"),
            "aud": payload.get("aud")
        }

    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"valid": False}
        )

    except jwt.InvalidAudienceError:
        return JSONResponse(
            status_code=401,
            content={"valid": False}
        )

    except jwt.InvalidIssuerError:
        return JSONResponse(
            status_code=401,
            content={"valid": False}
        )

    except jwt.InvalidSignatureError:
        return JSONResponse(
            status_code=401,
            content={"valid": False}
        )

    except jwt.InvalidTokenError:
        return JSONResponse(
            status_code=401,
            content={"valid": False}
        )

    except Exception:
        return JSONResponse(
            status_code=401,
            content={"valid": False}
        )
    
    # ==========================================================
# Q3 : 12-Factor Configuration
# ==========================================================

DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 8000,
    "debug": False,
    "log_level": "INFO"
}


def load_yaml_config():
    if os.path.exists("config.yaml"):
        with open("config.yaml", "r") as f:
            data = yaml.safe_load(f)
            if data:
                return data
    return {}


def load_env_config():
    cfg = {}

    if os.getenv("HOST"):
        cfg["host"] = os.getenv("HOST")

    if os.getenv("PORT"):
        cfg["port"] = int(os.getenv("PORT"))

    if os.getenv("DEBUG"):
        cfg["debug"] = os.getenv("DEBUG").lower() == "true"

    if os.getenv("LOG_LEVEL"):
        cfg["log_level"] = os.getenv("LOG_LEVEL")

    return cfg


@app.get("/effective-config")
def effective_config(set: str | None = None):

    config = DEFAULT_CONFIG.copy()

    # config.yaml
    config.update(load_yaml_config())

    # Environment variables
    config.update(load_env_config())

    # Query override
    if set:
        try:
            key, value = set.split("=", 1)

            if key == "port":
                value = int(value)

            elif key == "debug":
                value = value.lower() == "true"

            config[key] = value

        except Exception:
            pass

    return config

# ==========================================================
# Q5 : Analytics Endpoint
# ==========================================================

@app.post("/analytics")
def analytics(
    event: AnalyticsEvent,
    x_api_key: str | None = Header(default=None)
):
    # API Key validation
    if x_api_key != API_KEY:
        return JSONResponse(
            status_code=401,
            content={
                "success": False,
                "message": "Invalid API Key"
            }
        )

    analytics_events.append(
        {
            "event": event.event,
            "value": event.value
        }
    )

    return {
        "success": True,
        "total_events": len(analytics_events)
    }


@app.get("/analytics")
def analytics_summary():

    if not analytics_events:
        return {
            "count": 0,
            "sum": 0,
            "average": 0
        }

    total = sum(item["value"] for item in analytics_events)

    return {
        "count": len(analytics_events),
        "sum": total,
        "average": total / len(analytics_events)
    }

# ==========================================================
# Q6 : Production Observability
# ==========================================================

@app.get("/work")
def work(n: int = 1000):
    """
    Simulate some work while incrementing the Prometheus counter.
    """
    total = 0

    for i in range(n):
        total += i * i

    logger.info("Processed work with n=%d", n)

    return {
        "success": True,
        "n": n,
        "result": total
    }


@app.get("/metrics")
def metrics():
    return PlainTextResponse(
        generate_latest().decode(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/healthz")
def healthz():
    return {
        "status": "ok"
    }


@app.get("/logs/tail")
def logs_tail(lines: int = 20):

    logfile = "logs/app.log"

    if not os.path.exists(logfile):
        return {
            "logs": []
        }

    with open(logfile, "r") as f:
        content = f.readlines()

    return {
        "logs": [line.rstrip() for line in content[-lines:]]
    }