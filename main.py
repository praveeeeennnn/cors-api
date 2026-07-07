from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Your email
EMAIL = "23f2000083@ds.study.iitm.ac.in"

# Question 5 API Key
API_KEY = "ak_97er7aozc34h0tkccrf8j8yb"

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Models
# -----------------------------

class Event(BaseModel):
    user: str
    amount: float
    ts: int

class AnalyticsRequest(BaseModel):
    events: List[Event]

# -----------------------------
# Home
# -----------------------------

@app.get("/")
def home():
    return {"message": "Analytics API Running"}

# -----------------------------
# Question 5 Endpoint
# -----------------------------

@app.post("/analytics")
def analytics(
    request: AnalyticsRequest,
    x_api_key: str = Header(default=None)
):
    # Authenticate
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    total_events = len(request.events)

    unique_users = len({event.user for event in request.events})

    revenue = 0.0
    user_totals = {}

    for event in request.events:
        if event.amount > 0:
            revenue += event.amount
            user_totals[event.user] = user_totals.get(event.user, 0) + event.amount

    top_user = max(user_totals, key=user_totals.get) if user_totals else ""

    return {
        "email": EMAIL,
        "total_events": total_events,
        "unique_users": unique_users,
        "revenue": revenue,
        "top_user": top_user
    }