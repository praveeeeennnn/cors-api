from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    model: str
    messages: list
    stream: bool = False


@app.post("/v1/chat/completions")
def chat(req: ChatRequest):

    user_message = req.messages[-1]["content"]

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": req.model,
            "prompt": user_message,
            "stream": False
        }
    )

    result = response.json()

    return {
        "id": "ollama-response",
        "object": "chat.completion",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result["response"]
                }
            }
        ]
    }