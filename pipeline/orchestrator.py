import os
from typing import Any

from pydantic import BaseModel, Field

from agents.code_generator import CodeGeneratorAgent
from agents.prd_analysis import PRDAnalysisAgent
from agents.ui_planner import UIPlannerAgent
from memory.store import MemoryStore
from schemas.code_gen import CodeGenResult
from schemas.prd_analysis import PRDAnalysisResult
from schemas.ui_plan import UIPlan
from tools.tailwind_search import search_for_components


class AgentStep(BaseModel):
    agent: str
    status: str
    summary: str = ""


class ToolCallRecord(BaseModel):
    tool: str
    input: dict[str, Any]
    output: dict[str, Any]


class PipelineResult(BaseModel):
    steps: list[AgentStep] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    memory_display: str = ""
    analysis: dict[str, Any] | None = None
    ui_plan: dict[str, Any] | None = None
    code: dict[str, Any] | None = None
    component_tree: list[str] = Field(default_factory=list)
    error: str | None = None


class PipelineOrchestrator:
    """Runs Agents 1→2→3 with memory + Tailwind search tool calls."""

    def __init__(
        self,
        *,
        memory_path: str = "data/memory.json",
        model: str | None = None,
        mock: bool = False,
    ) -> None:
        self.memory = MemoryStore(memory_path)
        self.model = model
        self.mock = mock or not os.getenv("OPENAI_API_KEY")

    def run(self, prd_text: str, *, save_memory: bool = True) -> PipelineResult:
        result = PipelineResult(memory_display=self.memory.format_display())
        prd_text = prd_text.strip()
        if not prd_text:
            result.error = "PRD text is empty"
            return result

        memory_ctx = self.memory.context_for_agents()

        try:
            if self.mock:
                return self._run_mock(prd_text, save_memory=save_memory)

            # Agent 1
            result.steps.append(
                AgentStep(agent="Agent 1 — PRD Analysis", status="running")
            )
            agent1 = PRDAnalysisAgent(model=self.model)
            analysis = agent1.analyze(prd_text)
            result.analysis = analysis.model_dump()
            result.steps[-1] = AgentStep(
                agent="Agent 1 — PRD Analysis",
                status="done",
                summary=f"{len(analysis.devices)} devices, {len(analysis.widgets)} widgets",
            )

            # Agent 2
            result.steps.append(
                AgentStep(agent="Agent 2 — UI Planner", status="running")
            )
            agent2 = UIPlannerAgent(model=self.model)
            ui_plan = agent2.plan(analysis, memory_context=memory_ctx)
            result.ui_plan = ui_plan.model_dump()
            widgets = ui_plan.layout.main_widgets
            result.component_tree = self._build_tree(ui_plan)
            result.steps[-1] = AgentStep(
                agent="Agent 2 — UI Planner",
                status="done",
                summary=f"layout: sidebar={ui_plan.layout.sidebar}, {len(widgets)} widgets",
            )

            # Tool calls (before Agent 3)
            tool_matches = search_for_components(widgets)
            for match in tool_matches:
                result.tool_calls.append(
                    ToolCallRecord(
                        tool="searchTailwindComponent",
                        input={"widgetType": match.widget_type},
                        output={
                            "component": match.component,
                            "style": match.style,
                            "classes": match.classes,
                        },
                    )
                )

            # Agent 3
            result.steps.append(
                AgentStep(
                    agent="Agent 3 — Code Generator (+ tool hints)",
                    status="running",
                )
            )
            agent3 = CodeGeneratorAgent(model=self.model)
            tool_hints = [m.model_dump() for m in tool_matches]
            code = agent3.generate(
                ui_plan,
                memory_context=memory_ctx,
                tool_results=tool_hints,
            )
            result.code = code.model_dump()
            result.steps[-1] = AgentStep(
                agent="Agent 3 — Code Generator (+ tool hints)",
                status="done",
                summary=f"{len(code.components)} components generated",
            )

            if save_memory:
                rec = self.memory.save_prd(prd_text, result.analysis)
                self.memory.save_layout(result.ui_plan, prd_id=rec.id)

            result.memory_display = self.memory.format_display()
            return result

        except Exception as exc:
            result.error = str(exc)
            if result.steps and result.steps[-1].status == "running":
                result.steps[-1].status = "error"
            return result

    def _build_tree(self, ui_plan: UIPlan) -> list[str]:
        tree = ["DashboardPage"]
        if ui_plan.layout.topbar:
            tree.append("├── TopBar")
        if ui_plan.layout.sidebar:
            tree.append("├── SidebarNav")
        tree.append("└── Main")
        for i, w in enumerate(ui_plan.layout.main_widgets):
            prefix = "    ├── " if i < len(ui_plan.layout.main_widgets) - 1 else "    └── "
            tree.append(f"{prefix}{w}")
        return tree

    def _run_mock(self, prd_text: str, *, save_memory: bool) -> PipelineResult:
        """Demo path without OpenAI — still runs the Tailwind search tool."""
        from tools.tailwind_search import search_tailwind_component

        result = PipelineResult()
        result.steps = [
            AgentStep(
                agent="Agent 1 — PRD Analysis",
                status="done",
                summary="[mock] 2 devices, 5 widgets",
            ),
            AgentStep(
                agent="Agent 2 — UI Planner",
                status="done",
                summary="[mock] sidebar + topbar, 3 widgets",
            ),
        ]
        result.analysis = {
            "devices": ["temperature sensor", "smart meter"],
            "widgets": ["line chart", "KPI card", "alert panel"],
        }
        result.ui_plan = {
            "layout": {
                "sidebar": True,
                "topbar": True,
                "main_widgets": ["DeviceCard", "AlertPanel", "LineChartCard"],
            }
        }
        result.component_tree = self._build_tree(UIPlan.model_validate(result.ui_plan))

        for wtype in ("chart", "alert", "card"):
            match = search_tailwind_component(wtype)
            result.tool_calls.append(
                ToolCallRecord(
                    tool="searchTailwindComponent",
                    input={"widgetType": wtype},
                    output={
                        "component": match.component,
                        "style": match.style,
                        "classes": match.classes,
                    },
                )
            )

        chart = search_tailwind_component("chart")
        result.code = {
            "components": [
                {
                    "name": "DeviceCard",
                    "code": f'''export function DeviceCard() {{
  return (
    <div className="{chart.classes}">
      <h2 className="text-lg font-semibold">Temperature Sensor</h2>
      <p className="text-sm text-slate-500">Online · 22.4°C</p>
    </div>
  );
}}''',
                },
                {
                    "name": "LineChartCard",
                    "code": '''export function LineChartCard() {
  return (
    <div className="rounded-lg border p-4 min-h-[240px] w-full">
      <h3 className="font-medium">Energy — Line Chart</h3>
      <div className="mt-4 h-40 bg-slate-100 rounded flex items-center justify-center text-slate-400">
        Chart placeholder
      </div>
    </div>
  );
}''',
                },
            ],
            "entrypoint": None,
        }
        result.steps.append(
            AgentStep(
                agent="Agent 3 — Code Generator (+ tool hints)",
                status="done",
                summary="[mock] 2 components (tool: searchTailwindComponent)",
            )
        )
        if save_memory:
            self.memory.save_prd(prd_text, result.analysis)
            self.memory.save_layout(result.ui_plan)
        result.memory_display = self.memory.format_display()
        return result
