"""
LiteLLM async post-call hook: strip markdown JSON fences from Claude responses.

Claude wraps JSON in ```json ... ``` fences. Graphify expects raw parseable JSON
via json.loads(). This hook detects markdown-wrapped content and unwraps it.

Loaded via litellm-config.yaml -> general_settings.callbacks
"""
import re
from typing import Any, Dict

# Regex to match markdown code fences at start (optionally with language) and end
_FENCE_START = re.compile(r"^\s*```(?:json|JSON)?\s*\n?", flags=re.MULTILINE)
_FENCE_END = re.compile(r"\n?\s*```\s*$", flags=re.MULTILINE)


def strip_markdown_fences(content: str) -> str:
    """Remove leading ```json fence and trailing ``` fence if present."""
    if not isinstance(content, str):
        return content
    stripped = content.strip()
    if stripped.startswith("```"):
        # Remove first line if it's the opening fence
        stripped = _FENCE_START.sub("", stripped, count=1)
    if stripped.rstrip().endswith("```"):
        stripped = _FENCE_END.sub("", stripped, count=1)
    return stripped.strip()


# LiteLLM custom callback class
from litellm.integrations.custom_logger import CustomLogger


class MarkdownStripperLogger(CustomLogger):
    """Strip markdown JSON fences from response content (post-call hook)."""

    async def async_post_call_success_hook(
        self,
        data: Dict[str, Any],
        user_api_key_dict: Any,
        response: Any,
    ) -> Any:
        """Mutate the response in-place to strip markdown fences."""
        import sys
        try:
            choices = getattr(response, "choices", None) or response.get("choices", [])
            for idx, choice in enumerate(choices):
                msg = getattr(choice, "message", None) or choice.get("message", {})
                content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else None)
                preview_in = (content[:200] if isinstance(content, str) else repr(content))
                print(f"[markdown_stripper] IN  choice={idx} len={len(content) if isinstance(content, str) else 0} preview={preview_in!r}", file=sys.stderr, flush=True)
                if not content:
                    continue
                cleaned = strip_markdown_fences(content)
                preview_out = cleaned[:200] if isinstance(cleaned, str) else repr(cleaned)
                print(f"[markdown_stripper] OUT choice={idx} len={len(cleaned)} preview={preview_out!r}", file=sys.stderr, flush=True)
                if cleaned != content:
                    if hasattr(msg, "content"):
                        msg.content = cleaned
                    elif isinstance(msg, dict):
                        msg["content"] = cleaned
        except Exception as e:
            print(f"[markdown_stripper] hook error (non-fatal): {e}", file=sys.stderr, flush=True)
        return response


# Instance for LiteLLM to import
proxy_handler_instance = MarkdownStripperLogger()
