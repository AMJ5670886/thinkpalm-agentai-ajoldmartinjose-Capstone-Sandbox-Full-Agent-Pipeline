"""Shared OpenAI-compatible chat helpers with Groq-safe structured output."""

from __future__ import annotations

import json
import os
from typing import Any, TypeVar

from openai import OpenAI
from pydantic import BaseModel, ValidationError

# Groq structured-output support (https://console.groq.com/docs/structured-outputs)
_GROQ_STRICT_MODELS = frozenset(
    {
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
    }
)
_GROQ_BEST_EFFORT_MODELS = _GROQ_STRICT_MODELS | frozenset(
    {
        "openai/gpt-oss-safeguard-20b",
        "meta-llama/llama-4-scout-17b-16e-instruct",
    }
)

T = TypeVar("T", bound=BaseModel)


def _base_url(base_url: str | None) -> str:
    return (base_url or os.getenv("GROQ_BASE_URL") or "").lower()


def _is_groq(base_url: str | None) -> bool:
    return "groq.com" in _base_url(base_url)


def _json_schema_mode() -> str:
    """auto | strict | off — controls response_format selection."""
    return os.getenv("OPENAI_JSON_SCHEMA", "auto").strip().lower()


def resolve_response_format(
    *,
    schema_name: str,
    schema: dict[str, Any],
    model: str,
    base_url: str | None = None,
) -> dict[str, Any]:
    mode = _json_schema_mode()

    if mode in ("0", "false", "off", "json_object", "none"):
        return {"type": "json_object"}

    if mode in ("1", "true", "strict", "json_schema"):
        return {
            "type": "json_schema",
            "json_schema": {
                "name": schema_name,
                "strict": True,
                "schema": schema,
            },
        }

    # auto
    if _is_groq(base_url):
        if model in _GROQ_STRICT_MODELS:
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": True,
                    "schema": schema,
                },
            }
        if model in _GROQ_BEST_EFFORT_MODELS:
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "strict": False,
                    "schema": schema,
                },
            }
        return {"type": "json_object"}

    return {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "strict": True,
            "schema": schema,
        },
    }


def _schema_hint(schema: dict[str, Any]) -> str:
    return (
        "\n\nRespond with a single JSON object that conforms to this JSON Schema "
        "(no markdown fences or extra text):\n"
        f"{json.dumps(schema, indent=2)}"
    )


def _with_schema_hint(
    messages: list[dict[str, str]], schema: dict[str, Any]
) -> list[dict[str, str]]:
    out = [dict(m) for m in messages]
    for i, msg in enumerate(out):
        if msg.get("role") == "system":
            out[i] = {
                **msg,
                "content": msg["content"] + _schema_hint(schema),
            }
            return out
    out.insert(0, {"role": "system", "content": _schema_hint(schema).lstrip()})
    return out


def _is_json_schema_rejected(exc: BaseException) -> bool:
    text = str(exc).lower()
    return "json_schema" in text and (
        "does not support" in text or "invalid_request" in text or "400" in text
    )


def structured_chat_completion(
    client: OpenAI,
    *,
    model: str,
    messages: list[dict[str, str]],
    schema_name: str,
    schema: dict[str, Any],
    temperature: float,
    base_url: str | None = None,
) -> str:
    """Call chat.completions with the best structured format for the provider/model."""
    response_format = resolve_response_format(
        schema_name=schema_name,
        schema=schema,
        model=model,
        base_url=base_url,
    )
    request_messages = messages
    if response_format["type"] == "json_object":
        request_messages = _with_schema_hint(messages, schema)

    def _create(fmt: dict[str, Any], msgs: list[dict[str, str]]):
        return client.chat.completions.create(
            model=model,
            messages=msgs,
            response_format=fmt,
            temperature=temperature,
        )

    try:
        response = _create(response_format, request_messages)
    except Exception as exc:
        if response_format["type"] != "json_schema" or not _is_json_schema_rejected(
            exc
        ):
            raise
        response = _create(
            {"type": "json_object"},
            _with_schema_hint(messages, schema),
        )

    raw = response.choices[0].message.content
    if not raw:
        raise RuntimeError("Model returned empty content.")
    return raw


def parse_structured_response(raw: str, model: type[T]) -> T:
    try:
        data = json.loads(raw)
        return model.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise RuntimeError(f"Failed to parse agent output: {exc}") from exc
