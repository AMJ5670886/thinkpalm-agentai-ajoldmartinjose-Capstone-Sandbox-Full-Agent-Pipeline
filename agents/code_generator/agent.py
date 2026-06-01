import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from agents.llm import parse_structured_response, structured_chat_completion
from agents.code_generator.prompts import (
    MEMORY_SECTION,
    SYSTEM_PROMPT,
    TOOL_SECTION,
    USER_PROMPT_TEMPLATE,
)
from schemas.code_gen import CodeGenResult
from schemas.ui_plan import UIPlan

load_dotenv()


class CodeGeneratorAgent:
    """Agent 3 — generates React + Tailwind component code from a UI plan."""

    def __init__(
        self,
        *,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.model = model or os.getenv("GROQ_MODEL", "gpt-4o-mini")
        self._base_url = base_url or os.getenv("GROQ_BASE_URL")
        self._client = OpenAI(
            api_key=api_key or os.getenv("GROQAI_API_KEY"),
            base_url=self._base_url,
        )

    def generate(
        self,
        ui_plan: UIPlan,
        *,
        memory_context: dict | None = None,
        tool_results: list[dict] | None = None,
    ) -> CodeGenResult:
        """Generate React + Tailwind code for the given UI plan."""
        ui_plan_json = ui_plan.model_dump_json()
        memory_block = ""
        if memory_context:
            memory_block = MEMORY_SECTION.format(
                memory_json=json.dumps(memory_context, indent=2)
            )
        tool_block = ""
        if tool_results:
            tool_block = TOOL_SECTION.format(
                tool_results_json=json.dumps(tool_results, indent=2)
            )

        raw = structured_chat_completion(
            self._client,
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(
                        ui_plan_json=ui_plan_json,
                        memory_block=memory_block,
                        tool_block=tool_block,
                    ),
                },
            ],
            schema_name="code_gen_result",
            schema=CodeGenResult.model_json_schema(),
            temperature=0.3,
            base_url=self._base_url,
        )
        return parse_structured_response(raw, CodeGenResult)

