"""FastAPI backend for the IoT Dashboard Generator UI."""

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from memory.store import MemoryStore
from pipeline.orchestrator import PipelineOrchestrator
from tools.tailwind_search import search_tailwind_component

load_dotenv()

app = FastAPI(title="IoT Dashboard Generator API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    prd: str = Field(min_length=1)
    mock: bool = False


class ToolSearchRequest(BaseModel):
    widget_type: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/memory")
def get_memory() -> dict[str, Any]:
    store = MemoryStore()
    data = store.load()
    return {
        "display": store.format_display(),
        "data": data.model_dump(),
    }


@app.post("/api/tools/search-tailwind")
def api_search_tailwind(body: ToolSearchRequest) -> dict[str, Any]:
    """Expose searchTailwindComponent as an HTTP tool endpoint."""
    match = search_tailwind_component(body.widget_type)
    return {
        "tool": "searchTailwindComponent",
        "input": {"widgetType": body.widget_type},
        "output": {
            "component": match.component,
            "style": match.style,
            "classes": match.classes,
        },
    }


@app.post("/api/generate")
def generate(body: GenerateRequest) -> dict[str, Any]:
    use_mock = body.mock or os.getenv("MOCK_PIPELINE", "").lower() in ("1", "true")
    orchestrator = PipelineOrchestrator(mock=use_mock)
    result = orchestrator.run(body.prd)
    return result.model_dump()
