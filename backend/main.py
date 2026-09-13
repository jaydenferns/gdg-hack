from datetime import datetime, timezone
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import database
from ai_provider import provider

app = FastAPI(title="Guardian AI API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class AnalyzeRequest(BaseModel):
    message: str = Field(min_length=1, max_length=3000)
    conversation: list[str] = Field(default_factory=list, max_length=200)

class CaseRequest(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    risk_level: Literal["low", "medium", "high"]
    language: str
    indicators: list[str]
    explanation: str
    recommended_action: str
    conversation: list[dict]
    timeline: list[dict] = Field(default_factory=list)
    status: str = "Reviewing"

class StatusRequest(BaseModel):
    status: Literal["Reviewing", "Escalated", "Resolved", "Dismissed"]

@app.on_event("startup")
def startup() -> None: database.initialize()

@app.get("/")
def health(): return {"service": "Guardian AI", "mode": "local-first"}

@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    result = provider.analyze(request.message, request.conversation)
    return result.__dict__

@app.post("/cases", status_code=201)
def create_case(request: CaseRequest):
    data = request.model_dump()
    data["created_at"] = datetime.now(timezone.utc).isoformat()
    return database.create_case(data)

@app.get("/cases")
def cases(): return database.list_cases()

@app.get("/cases/{case_code}")
def case(case_code: str):
    result = database.get_case(case_code)
    if not result: raise HTTPException(404, "Case not found")
    return result

@app.patch("/cases/{case_code}")
def patch_case(case_code: str, request: StatusRequest):
    result = database.update_case(case_code, request.status)
    if not result: raise HTTPException(404, "Case not found")
    return result
