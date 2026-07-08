from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt
from cryptography.hazmat.primitives import serialization
import uuid
import time
import os
from typing import List


app = FastAPI(title="TDS Exam API")

EMAIL = "23f2000083@ds.study.iitm.ac.in"


# ============================================================
# CORS
# ============================================================

ALLOWED_ORIGINS = [
    "https://dash-rnh108.example.com",
    "THE_Q3_ORIGIN_HERE"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=[
        "X-Request-ID",
        "X-Process-Time"
    ],
)


# ============================================================
# Middleware Headers
# ============================================================

@app.middleware("http")
async def add_headers(request: Request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    response.headers["X-Request-ID"] = str(uuid.uuid4())
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.6f}"

    return response


# ============================================================
# Home
# ============================================================

@app.get("/")
def home():
    return {
        "message": "TDS Exam API Running"
    }


# ============================================================
# QUESTION 1
# CORS-Aware Metrics API
# ============================================================

@app.get("/stats")
def stats(values: str = Query(...)):

    nums = [
        int(x.strip())
        for x in values.split(",")
        if x.strip()
    ]

    return {
        "email": EMAIL,
        "count": len(nums),
        "sum": sum(nums),
        "min": min(nums),
        "max": max(nums),
        "mean": sum(nums) / len(nums),
    }


# ============================================================
# QUESTION 2
# OAuth 2.0 / OIDC JWT Verification
# ============================================================

ISSUER = "https://idp.exam.local"

AUDIENCE = "tds-f1cwzwuq.apps.exam.local"


PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""


PUBLIC_KEY = serialization.load_pem_public_key(
    PUBLIC_KEY_PEM
)


class VerifyRequest(BaseModel):
    token: str



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
            "aud": payload.get("aud"),
        }


    except jwt.PyJWTError:

        return JSONResponse(
            status_code=401,
            content={
                "valid": False
            }
        )



# ============================================================
# QUESTION 3
# 12-Factor Config Precedence
# ============================================================


DEFAULTS = {

    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000"

}


# .env layer

DOTENV = {

    "workers": 10,
    "log_level": "warning",
    "api_key": "key-0my3jzlhk0"

}



def to_bool(value):

    return str(value).lower() in (
        "true",
        "1",
        "yes",
        "on"
    )



@app.get("/effective-config")
def effective_config(
    set: List[str] = Query(default=[])
):

    config = DEFAULTS.copy()


    # config.development.yaml
    # empty


    # .env layer

    config.update(DOTENV)



    # OS Environment layer
    # APP_* prefix

    config["workers"] = int(
        os.getenv(
            "APP_WORKERS",
            "10"
        )
    )


    config["debug"] = to_bool(
        os.getenv(
            "APP_DEBUG",
            "true"
        )
    )


    config["log_level"] = os.getenv(
        "APP_LOG_LEVEL",
        "error"
    )


    config["api_key"] = os.getenv(
        "APP_API_KEY",
        "key-0my3jzlhk0"
    )



    # CLI overrides (highest priority)

    for item in set:

        if "=" not in item:
            continue


        key, value = item.split("=", 1)


        if key in (
            "port",
            "workers"
        ):

            config[key] = int(value)


        elif key == "debug":

            config[key] = to_bool(value)


        else:

            config[key] = value



    # Mask secret always

    config["api_key"] = "****"


    return config