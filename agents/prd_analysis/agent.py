import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agents.llm import parse_structured_response, structured_chat_completion
from agents.prd_analysis.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from schemas.prd_analysis import PRDAnalysisResult

load_dotenv()


class PRDAnalysisAgent:
    """Agent 1 — reads an IoT PRD and extracts devices and dashboard widgets."""

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

    def analyze(self, prd_text: str) -> PRDAnalysisResult:
        """Run PRD analysis and return validated structured output."""
        prd_text = prd_text.strip()
        if not prd_text:
            raise ValueError("PRD text is empty.")

        raw = structured_chat_completion(
            self._client,
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": USER_PROMPT_TEMPLATE.format(prd_text=prd_text),
                },
            ],
            schema_name="prd_analysis",
            schema=PRDAnalysisResult.model_json_schema(),
            temperature=0.2,
            base_url=self._base_url,
        )
        return parse_structured_response(raw, PRDAnalysisResult)

    def analyze_file(self, path: str | Path) -> PRDAnalysisResult:
        """Load a PRD from disk and analyze it."""
        prd_path = Path(path)
        if not prd_path.is_file():
            raise FileNotFoundError(f"PRD file not found: {prd_path}")
        return self.analyze(prd_path.read_text(encoding="utf-8"))
