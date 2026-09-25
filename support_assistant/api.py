from fastapi import FastAPI
from pydantic import BaseModel, Field

from assistant import ask_assistant


app = FastAPI(
    title="Zepto Support Assistant",
    description="Policy-based customer support assistant using LangGraph and ChromaDB",
    version="1.0.0",
)


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1)


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float = Field(..., ge=0.0, le=1.0)


@app.get("/")
def root():
    return {
        "message": "Zepto Support Assistant API is running"
    }


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    result = ask_assistant(request.query)

    return AskResponse(
        answer=result["answer"],
        sources=result["sources"],
        confidence=result["confidence"],
    )