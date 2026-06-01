from pydantic import BaseModel, Field


class PRDAnalysisResult(BaseModel):
    """Structured output from Agent 1 — PRD Analysis Agent."""

    devices: list[str] = Field(
        default_factory=list,
        description="IoT device types mentioned in the PRD (e.g. temperature sensor, smart meter).",
    )
    widgets: list[str] = Field(
        default_factory=list,
        description=(
            "Dashboard widgets derived from KPIs, charts, alerts, tables, and controls "
            "(e.g. line chart, KPI card, alert panel)."
        ),
    )
