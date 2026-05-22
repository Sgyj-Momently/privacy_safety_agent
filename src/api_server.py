"""FastAPI entrypoint for the privacy safety agent."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

from .privacy_guard import screen_bundle

app = FastAPI(title="Privacy Safety Agent API", version="0.1.0")

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


class PrivacySafetyRequest(BaseModel):
    project_id: str = Field(min_length=1)
    photos: list[dict[str, Any]] = Field(default_factory=list)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "privacy_safety_agent"}


@app.post("/api/v1/privacy-safety")
def review_privacy(request: PrivacySafetyRequest) -> dict[str, Any]:
    return {"project_id": request.project_id, **screen_bundle(request.model_dump())}

