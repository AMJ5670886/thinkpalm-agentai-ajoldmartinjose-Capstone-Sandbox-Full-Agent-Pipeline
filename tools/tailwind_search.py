"""Custom tool: searchTailwindComponent(widgetType) for IoT dashboard widgets."""

from pydantic import BaseModel, Field

# Registry: widget type -> recommended component + Tailwind style hints
_COMPONENT_REGISTRY: dict[str, dict[str, str]] = {
    "chart": {
        "component": "LineChartCard",
        "style": "responsive",
        "classes": "rounded-lg border bg-card p-4 shadow-sm min-h-[240px]",
    },
    "line chart": {
        "component": "LineChartCard",
        "style": "responsive",
        "classes": "rounded-lg border p-4 min-h-[240px] w-full",
    },
    "bar chart": {
        "component": "BarChartCard",
        "style": "responsive",
        "classes": "rounded-lg border p-4 min-h-[220px]",
    },
    "kpi": {
        "component": "KpiStatCard",
        "style": "compact",
        "classes": "rounded-xl bg-white p-6 shadow-lg dark:bg-slate-800",
    },
    "card": {
        "component": "DeviceCard",
        "style": "elevated",
        "classes": "bg-white shadow-lg rounded-lg p-4 dark:bg-slate-800",
    },
    "device": {
        "component": "DeviceStatusCard",
        "style": "elevated",
        "classes": "bg-white shadow-md rounded-lg p-4 border",
    },
    "alert": {
        "component": "AlertPanel",
        "style": "stacked",
        "classes": "border-l-4 border-amber-500 bg-amber-50 p-4 rounded-r-lg",
    },
    "table": {
        "component": "DataTable",
        "style": "scrollable",
        "classes": "overflow-x-auto rounded-lg border shadow-sm",
    },
    "control": {
        "component": "ControlPanel",
        "style": "inline",
        "classes": "flex flex-wrap gap-4 p-4 rounded-lg bg-slate-50",
    },
    "toggle": {
        "component": "ToggleControl",
        "style": "inline",
        "classes": "inline-flex items-center gap-2",
    },
    "sidebar": {
        "component": "SidebarNav",
        "style": "fixed",
        "classes": "w-64 min-h-screen bg-slate-900 text-slate-50 p-4",
    },
    "topbar": {
        "component": "TopBar",
        "style": "sticky",
        "classes": "sticky top-0 z-10 border-b bg-white/80 backdrop-blur px-6 py-3",
    },
}

_NAME_HINTS: list[tuple[str, str]] = [
    ("chart", "chart"),
    ("line", "line chart"),
    ("bar", "bar chart"),
    ("kpi", "kpi"),
    ("stat", "kpi"),
    ("gauge", "kpi"),
    ("device", "device"),
    ("alert", "alert"),
    ("alarm", "alert"),
    ("table", "table"),
    ("toggle", "toggle"),
    ("control", "control"),
    ("slider", "control"),
    ("panel", "card"),
    ("card", "card"),
]


class TailwindComponentMatch(BaseModel):
    """Result of searchTailwindComponent tool call."""

    widget_type: str
    component: str
    style: str
    classes: str = Field(default="", description="Suggested Tailwind utility classes")


def search_tailwind_component(widget_type: str) -> TailwindComponentMatch:
    """
    Custom tool: look up a recommended Tailwind/React component for a widget type.

    Example:
        search_tailwind_component("chart")
        -> TailwindComponentMatch(component="LineChartCard", style="responsive", ...)
    """
    key = widget_type.strip().lower()
    if key in _COMPONENT_REGISTRY:
        entry = _COMPONENT_REGISTRY[key]
        return TailwindComponentMatch(
            widget_type=widget_type,
            component=entry["component"],
            style=entry["style"],
            classes=entry.get("classes", ""),
        )

    for hint, registry_key in _NAME_HINTS:
        if hint in key:
            entry = _COMPONENT_REGISTRY[registry_key]
            return TailwindComponentMatch(
                widget_type=widget_type,
                component=entry["component"],
                style=entry["style"],
                classes=entry.get("classes", ""),
            )

    return TailwindComponentMatch(
        widget_type=widget_type,
        component="GenericWidget",
        style="default",
        classes="rounded-lg border p-4 shadow-sm",
    )


def infer_widget_type(component_name: str) -> str:
    """Map PascalCase component name to a widget type for tool lookup."""
    name = component_name.lower()
    for hint, widget_type in _NAME_HINTS:
        if hint in name:
            return widget_type
    return "card"


def search_for_components(component_names: list[str]) -> list[TailwindComponentMatch]:
    """Run the tool for each planned component (Agent 3 pre-step)."""
    results: list[TailwindComponentMatch] = []
    seen: set[str] = set()
    for name in component_names:
        wtype = infer_widget_type(name)
        if wtype in seen:
            continue
        seen.add(wtype)
        results.append(search_tailwind_component(wtype))
    return results
