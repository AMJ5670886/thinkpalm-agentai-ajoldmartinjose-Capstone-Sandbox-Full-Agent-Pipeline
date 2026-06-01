from pydantic import BaseModel, Field


class ComponentCode(BaseModel):
    """Single generated React component."""

    name: str = Field(
        description="Component name, e.g. DeviceCard, AlertPanel, EnergyChart."
    )
    code: str = Field(
        description="React/TypeScript JSX source code for this component."
    )


class CodeGenResult(BaseModel):
    """Structured output from Agent 3 — Code Generator Agent."""

    components: list[ComponentCode] = Field(
        default_factory=list,
        description="List of generated React components.",
    )
    entrypoint: str | None = Field(
        default=None,
        description="Optional root component code (e.g. DashboardPage) wiring everything together.",
    )

