from pydantic import BaseModel, Field


class LayoutConfig(BaseModel):
    """High-level layout settings for the dashboard shell."""

    sidebar: bool = Field(
        default=True,
        description="Whether the dashboard uses a left sidebar for navigation/filters.",
    )
    topbar: bool = Field(
        default=True,
        description="Whether the dashboard has a top bar with title and global actions.",
    )
    main_widgets: list[str] = Field(
        default_factory=list,
        description="Primary widget components rendered in the main content area (e.g. DeviceCard, AlertPanel).",
    )


class UIPlan(BaseModel):
    """Structured output from Agent 2 — UI Planner Agent."""

    layout: LayoutConfig = Field(
        description="Top-level layout configuration and main widget ordering."
    )

