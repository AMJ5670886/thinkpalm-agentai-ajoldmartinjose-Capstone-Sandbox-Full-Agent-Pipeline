from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class UserPreferences(BaseModel):
    """Saved user defaults applied to future generations."""

    theme: str = Field(default="light", description="light or dark")
    chart_preference: str = Field(
        default="line",
        description="Preferred chart type: line, bar, area, pie",
    )
    sidebar_default: bool = Field(default=True)
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional preference keys (e.g. density, accentColor).",
    )


class PRDRecord(BaseModel):
    """A previously analyzed PRD stored in memory."""

    id: str
    summary: str
    prd_text: str
    analysis: dict[str, Any]
    created_at: str = Field(default_factory=_utc_now)


class LayoutRecord(BaseModel):
    """A previously generated UI layout stored in memory."""

    id: str
    ui_plan: dict[str, Any]
    prd_id: str | None = None
    created_at: str = Field(default_factory=_utc_now)


class PipelineMemory(BaseModel):
    """Full persisted memory for the IoT dashboard pipeline."""

    preferences: UserPreferences = Field(default_factory=UserPreferences)
    previous_prds: list[PRDRecord] = Field(default_factory=list)
    generated_layouts: list[LayoutRecord] = Field(default_factory=list)
