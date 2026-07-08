from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import jwt
from cryptography.hazmat.primitives import serialization
import uuid
import time

app = FastAPI(title="TDS Exam API")

EMAIL = "23f2000083@ds.study.iitm.ac.in"

# -------------------------------
# Q1 CORS Settings
# -------------------------------
ALLOWED_ORIGIN = "https://dash-rnh108.example.com"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# -------------------------------
# Middleware
# -------------------------------
@app.middleware("http")
async def add_headers(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{duration:.6f}"

    return response


# -------------------------------
# Q2 JWT Settings
# -------------------------------
ISSUER = "https://idp.exam.local"

AUDIENCE = "tds-f1cwzwuq.apps.exam.local"

PUBLIC_KEY_PEM = b"""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4LlgniT7GlkL9Mce3b0wGLs9/7ZIXdQIDAQAB
-----END PUBLIC KEY-----"""

PUBLIC_KEY = serialization.load_pem_public_key(PUBLIC_KEY_PEM)


class VerifyRequest(BaseModel):
    token: str


@app.get("/")
def home():
    return {
        "message": "TDS API Running"
    }


# ============================================================
# Question 1
# ============================================================

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


# ============================================================
# Question 2
# ============================================================

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
            content={"valid": False},
        )