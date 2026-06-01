import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from agents.llm import parse_structured_response, structured_chat_completion
from agents.ui_planner.prompts import MEMORY_SECTION, SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from schemas.prd_analysis import PRDAnalysisResult
from schemas.ui_plan import UIPlan

load_dotenv()


class UIPlannerAgent:
    """Agent 2 — converts extracted requirements into a UI layout and component plan."""

    def __init__(
        self,
        *,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self._client = OpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=self._base_url,
        )

    def plan(
        self,
        analysis: PRDAnalysisResult,
        *,
        memory_context: dict | None = None,
    ) -> UIPlan:
        """Generate a UI plan from Agent 1's structured analysis."""
        requirements_json = analysis.model_dump_json()
        memory_block = ""
        if memory_context:
            memory_block = MEMORY_SECTION.format(
                memory_json=json.dumps(memory_context, indent=2)
            )

        raw = structured_chat_completion(
            self._client,
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(
                        requirements_json=requirements_json,
                        memory_block=memory_block,
                    ),
                },
            ],
            schema_name="ui_plan",
            schema=UIPlan.model_json_schema(),
            temperature=0.2,
            base_url=self._base_url,
        )
        return parse_structured_response(raw, UIPlan)

