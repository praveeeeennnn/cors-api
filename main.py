import time
import uuid
import jwt

from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel

# ==================================================
# CONFIGURATION
# ==================================================

EMAIL = "23f2000083@ds.study.iitm.ac.in"

# ---------------- Q1 ----------------
ALLOWED_ORIGIN = "https://dash-rnh108.example.com"

# ---------------- Q2 ----------------
ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-f1cwzwuq.apps.exam.local"

PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----
"""

# ---------------- Q3 ----------------

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# config.development.yaml is empty
YAML_CONFIG = {}

# .env values
ENV_FILE = {
    "workers": 10,
    "log_level": "warning",
    "api_key": "key-0my3jzlhk0",
}

# OS env values
OS_ENV = {
    "workers": 10,
    "debug": True,
    "log_level": "error",
}

# ==================================================
# APP
# ==================================================

app = FastAPI()

# ==================================================
# CORS
# ==================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        ALLOWED_ORIGIN,
        "https://exam.sanand.workers.dev"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# MIDDLEWARE
# ==================================================

class HeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):

        start = time.perf_counter()

        response = await call_next(request)

        process_time = time.perf_counter() - start

        response.headers["X-Request-ID"] = str(uuid.uuid4())
        response.headers["X-Process-Time"] = f"{process_time:.6f}"

        return response


app.add_middleware(HeaderMiddleware)

# ==================================================
# HOME
# ==================================================

@app.get("/")
def home():
    return {
        "message": "FastAPI Service Running"
    }

# ==================================================
# QUESTION 1
# ==================================================

@app.get("/stats")
def stats(values: str = Query(...)):

    numbers = [int(x.strip()) for x in values.split(",") if x.strip()]

    return {
        "email": EMAIL,
        "count": len(numbers),
        "sum": sum(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "mean": sum(numbers) / len(numbers)
    }

# ==================================================
# QUESTION 2
# ==================================================

class TokenRequest(BaseModel):
    token: str


@app.post("/verify")
def verify(data: TokenRequest):

    try:

        claims = jwt.decode(
            data.token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=AUDIENCE,
        )

        return {
            "valid": True,
            "email": claims.get("email", ""),
            "sub": claims.get("sub", ""),
            "aud": claims.get("aud", "")
        }

    except Exception:

        return JSONResponse(
            status_code=401,
            content={"valid": False}
        )

# ==================================================
# QUESTION 3
# ==================================================

@app.get("/effective-config")
def effective_config(request: Request):

    config = DEFAULTS.copy()

    # YAML
    config.update(YAML_CONFIG)

    # .env
    config.update(ENV_FILE)

    # OS ENV
    config.update(OS_ENV)

    # CLI overrides
    for item in request.query_params.getlist("set"):

        if "=" not in item:
            continue

        key, value = item.split("=", 1)

        key = key.strip()
        value = value.strip()

        if key in ["port", "workers"]:
            config[key] = int(value)

        elif key == "debug":
            config[key] = value.lower() in [
                "true",
                "1",
                "yes",
                "on",
            ]

        else:
            config[key] = value

    # Hide API key
    config["api_key"] = "****"

    return config