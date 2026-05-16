"""LiteLLM post-call hook for Graphify JSON extraction.

The hook keeps model output parseable without fabricating graph content:
- remove markdown JSON fences when the model returns fenced JSON;
- extract the outermost JSON object when the model adds a short preamble;
- return prose unchanged when no JSON object exists so Graphify can fail loudly.
"""

from __future__ import annotations

import sys
from typing import Any

from litellm.integrations.custom_logger import CustomLogger


def _clean_jsonish(content: str) -> str:
    text = content.strip()
    if text.startswith("```"):
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
        text = text.strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1].strip()
    return text


class JsonGuardLogger(CustomLogger):
    async def async_post_call_success_hook(
        self,
        data: dict[str, Any],
        user_api_key_dict: Any,
        response: Any,
    ) -> Any:
        try:
            choices = getattr(response, "choices", None) or response.get("choices", [])
            for idx, choice in enumerate(choices):
                msg = getattr(choice, "message", None) or choice.get("message", {})
                content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None)
                if not isinstance(content, str) or not content.strip():
                    continue
                cleaned = _clean_jsonish(content)
                print(
                    f"[json_guard] choice={idx} in_len={len(content)} out_len={len(cleaned)} "
                    f"in_preview={content[:120]!r} out_preview={cleaned[:120]!r}",
                    file=sys.stderr,
                    flush=True,
                )
                if cleaned != content:
                    if hasattr(msg, "content"):
                        msg.content = cleaned
                    elif isinstance(msg, dict):
                        msg["content"] = cleaned
        except Exception as exc:
            print(f"[json_guard] non-fatal hook error: {exc}", file=sys.stderr, flush=True)
        return response


proxy_handler_instance = JsonGuardLogger()
