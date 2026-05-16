"""Patch Graphify's Ollama transport for LiteLLM/Bedrock compatibility.

Graphify uses the Ollama backend as an OpenAI-compatible transport because
LiteLLM exposes Bedrock through /v1/chat/completions. The upstream Ollama path
adds Ollama-specific extra_body fields (`options`, `keep_alive`). Bedrock
rejects those fields. This patch keeps upstream behavior by default and only
skips the Ollama extra body when GRAPHIFY_DISABLE_OLLAMA_EXTRA_BODY=1.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import graphify.llm


path = Path(inspect.getfile(graphify.llm))
text = path.read_text(encoding="utf-8")
old = (
    '        keep_alive = os.environ.get("GRAPHIFY_OLLAMA_KEEP_ALIVE", "30m")\n'
    '        kwargs["extra_body"] = {"options": {"num_ctx": num_ctx}, "keep_alive": keep_alive}\n'
)
new = (
    '        keep_alive = os.environ.get("GRAPHIFY_OLLAMA_KEEP_ALIVE", "30m")\n'
    '        if os.environ.get("GRAPHIFY_DISABLE_OLLAMA_EXTRA_BODY") != "1":\n'
    '            kwargs["extra_body"] = {"options": {"num_ctx": num_ctx}, "keep_alive": keep_alive}\n'
)
if old not in text:
    raise SystemExit(f"Expected Graphify Ollama extra_body block not found in {path}")
path.write_text(text.replace(old, new), encoding="utf-8")
print(f"Patched {path} for LiteLLM/Bedrock transport")
