"""Check that an upstream can reply, call a tool, and stream a tool call."""

from __future__ import annotations

import asyncio

from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

from docu.core.config import Settings, get_settings

__all__ = ["main", "run_checks"]


@tool
def get_time(timezone: str) -> str:
    """Return the current time in an IANA timezone."""
    return timezone


async def run_checks(settings: Settings) -> dict[str, bool | str]:
    """Return one entry per check. ``True`` means it passed; a string is the failure."""
    model_id = settings.llm.model or "missing-model"
    try:
        model = init_chat_model(
            f"{settings.llm.provider}:{model_id}",
            base_url=settings.llm.upstream or None,
            api_key=settings.llm.api_key or "missing",
        )
    except Exception as exc:
        reason = str(exc).splitlines()[0][:200]
        return {"plain": reason, "tool_calls": reason, "stream": reason}

    results: dict[str, bool | str] = {}
    results["plain"] = await _plain(model)
    bound = model.bind_tools([get_time])
    results["tool_calls"] = await _tools(bound, stream=False)
    results["stream"] = await _tools(bound, stream=True)
    return results


async def _plain(model: object) -> bool | str:
    try:
        message = await model.ainvoke("Reply with the single word ok.")  # type: ignore[attr-defined]
    except Exception as exc:
        return str(exc).splitlines()[0][:200]
    text = getattr(message, "content", "")
    if isinstance(text, list):
        text = " ".join(str(part) for part in text)
    return True if str(text).strip() else "empty reply"


async def _tools(model: object, *, stream: bool) -> bool | str:
    prompt = "Call get_time for timezone UTC."
    try:
        if stream:
            saw = False
            async for chunk in model.astream(prompt):  # type: ignore[attr-defined]
                if getattr(chunk, "tool_call_chunks", None) or getattr(chunk, "tool_calls", None):
                    saw = True
            return True if saw else "stream had no tool call"
        message = await model.ainvoke(prompt)  # type: ignore[attr-defined]
    except Exception as exc:
        return str(exc).splitlines()[0][:200]
    return True if getattr(message, "tool_calls", None) else "no tool call"


def main() -> None:
    results = asyncio.run(run_checks(get_settings()))
    failed = False
    for name, value in results.items():
        if value is True:
            print(f"✓ {name}")
        else:
            print(f"✗ {name}: {value}")
            failed = True
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
