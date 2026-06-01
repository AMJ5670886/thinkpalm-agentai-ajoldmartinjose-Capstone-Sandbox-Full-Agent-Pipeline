import json
import uuid
from pathlib import Path
from typing import Any

from schemas.memory import LayoutRecord, PipelineMemory, PRDRecord, UserPreferences

DEFAULT_MEMORY_PATH = Path("data/memory.json")
MAX_PRD_HISTORY = 20
MAX_LAYOUT_HISTORY = 20


class MemoryStore:
    """Local JSON file memory: previous PRDs, layouts, and user preferences."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or DEFAULT_MEMORY_PATH)
        self._data: PipelineMemory | None = None

    def load(self) -> PipelineMemory:
        if self._data is not None:
            return self._data

        if self.path.is_file():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._data = PipelineMemory.model_validate(raw)
        else:
            self._data = PipelineMemory()

        return self._data

    def save(self) -> None:
        data = self.load()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(data.model_dump(), indent=2) + "\n",
            encoding="utf-8",
        )

    @property
    def preferences(self) -> UserPreferences:
        return self.load().preferences

    def update_preferences(self, **kwargs: Any) -> UserPreferences:
        data = self.load()
        known = {"theme", "chart_preference", "sidebar_default"}
        for key, value in kwargs.items():
            if key in known:
                setattr(data.preferences, key, value)
            else:
                data.preferences.extra[key] = value
        self.save()
        return data.preferences

    def save_prd(
        self,
        prd_text: str,
        analysis: dict[str, Any],
        *,
        summary: str | None = None,
    ) -> PRDRecord:
        data = self.load()
        record = PRDRecord(
            id=str(uuid.uuid4())[:8],
            summary=summary or _summarize_prd(prd_text),
            prd_text=prd_text,
            analysis=analysis,
        )
        data.previous_prds.append(record)
        data.previous_prds = data.previous_prds[-MAX_PRD_HISTORY:]
        self.save()
        return record

    def save_layout(
        self,
        ui_plan: dict[str, Any],
        *,
        prd_id: str | None = None,
    ) -> LayoutRecord:
        data = self.load()
        record = LayoutRecord(
            id=str(uuid.uuid4())[:8],
            ui_plan=ui_plan,
            prd_id=prd_id,
        )
        data.generated_layouts.append(record)
        data.generated_layouts = data.generated_layouts[-MAX_LAYOUT_HISTORY:]
        self.save()
        return record

    def context_for_agents(self) -> dict[str, Any]:
        """Preferences + light history hints passed into agent prompts."""
        data = self.load()
        last_layout = data.generated_layouts[-1] if data.generated_layouts else None
        last_prd = data.previous_prds[-1] if data.previous_prds else None
        recent_prds = [
            {
                "id": r.id,
                "summary": r.summary,
                "prd_text": r.prd_text,
                "devices": r.analysis.get("devices", []),
                "widgets": r.analysis.get("widgets", []),
            }
            for r in data.previous_prds[-3:]
        ]
        return {
            "preferences": data.preferences.model_dump(),
            "last_layout": last_layout.ui_plan if last_layout else None,
            "last_prd_summary": last_prd.summary if last_prd else None,
            "recent_prd_count": len(data.previous_prds),
            "recent_layout_count": len(data.generated_layouts),
            "recent_prds": recent_prds,
        }

    def format_display(self) -> str:
        """Human-readable memory snapshot for CLI / logs."""
        data = self.load()
        prefs = data.preferences.model_dump()
        lines = [
            "=== MEMORY ===",
            "User preferences:",
            json.dumps(prefs, indent=2),
            f"Previous PRDs stored: {len(data.previous_prds)}",
            f"Generated layouts stored: {len(data.generated_layouts)}",
        ]
        if data.previous_prds:
            last = data.previous_prds[-1]
            lines.append(f"Last PRD: [{last.id}] {last.summary[:80]}")
            lines.append("")
            lines.append("Recent PRD inputs (newest last):")
            for rec in data.previous_prds[-5:]:
                preview = _prd_preview(rec.prd_text, max_len=100)
                lines.append(f"  [{rec.id}] {preview}")
        if data.generated_layouts:
            last = data.generated_layouts[-1]
            widgets = last.ui_plan.get("layout", {}).get("main_widgets", [])
            lines.append(f"Last layout: [{last.id}] widgets={widgets}")
        lines.append("==============")
        return "\n".join(lines)


def _summarize_prd(prd_text: str, max_len: int = 120) -> str:
    one_line = " ".join(prd_text.split())
    if len(one_line) <= max_len:
        return one_line
    return one_line[: max_len - 3] + "..."


def _prd_preview(prd_text: str, max_len: int = 100) -> str:
    one_line = " ".join(prd_text.split())
    if len(one_line) <= max_len:
        return one_line
    return one_line[: max_len - 3] + "..."
