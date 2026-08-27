#!/usr/bin/env python3
"""Read-only Outlines import and signature smoke.

Run inside a Python environment where `outlines` is installed. The script does
not call models, providers, networks, or downloads.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import inspect
import json
import sys


def collect() -> dict[str, object]:
    import outlines
    from outlines import Generator, Template
    from outlines.applications import Application
    from outlines.backends import CFG_DEFAULT_BACKEND, JSON_SCHEMA_DEFAULT_BACKEND, REGEX_DEFAULT_BACKEND
    from outlines.inputs import Chat, Image, Audio, Video
    from outlines.types import CFG, Choice, JsonSchema, Regex
    from outlines.models import (
        from_anthropic,
        from_dottxt,
        from_gemini,
        from_llamacpp,
        from_lmstudio,
        from_mistral,
        from_mlxlm,
        from_ollama,
        from_openai,
        from_sglang,
        from_tgi,
        from_transformers,
        from_vllm,
        from_vllm_offline,
    )

    loaders = [
        from_anthropic,
        from_dottxt,
        from_gemini,
        from_llamacpp,
        from_lmstudio,
        from_mistral,
        from_mlxlm,
        from_ollama,
        from_openai,
        from_sglang,
        from_tgi,
        from_transformers,
        from_vllm,
        from_vllm_offline,
    ]

    template_output = Template.from_string("Hello {{ name }}")(name="Ada")
    return {
        "python": sys.version.split()[0],
        "distribution_version": importlib.metadata.version("outlines"),
        "module_file_present": bool(getattr(outlines, "__file__", None)),
        "chat_top_level_exported": hasattr(outlines, "Chat"),
        "signatures": {
            "Generator": str(inspect.signature(Generator)),
            "Template.from_string": str(inspect.signature(Template.from_string)),
            "Template.from_file": str(inspect.signature(Template.from_file)),
            "Application": str(inspect.signature(Application)),
            "Chat": str(inspect.signature(Chat)),
            "Image": str(inspect.signature(Image)),
            "Choice": str(inspect.signature(Choice)),
            "Regex": str(inspect.signature(Regex)),
            "JsonSchema": str(inspect.signature(JsonSchema)),
            "CFG": str(inspect.signature(CFG)),
            **{loader.__name__: str(inspect.signature(loader)) for loader in loaders},
        },
        "backend_defaults": {
            "cfg": CFG_DEFAULT_BACKEND,
            "json_schema": JSON_SCHEMA_DEFAULT_BACKEND,
            "regex": REGEX_DEFAULT_BACKEND,
        },
        "smoke": {
            "template": template_output,
            "chat_messages": Chat().messages,
            "regex_matches": Regex(r"[0-9]+").matches("123"),
            "choice_items": Choice(["a", "b"]).items,
            "input_classes": [Image.__name__, Audio.__name__, Video.__name__],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect installed Outlines public API without running models.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()
    try:
        payload = collect()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"outlines {payload['distribution_version']} on Python {payload['python']}")
        print(f"Chat top-level exported: {payload['chat_top_level_exported']}")
        print("Backend defaults:", payload["backend_defaults"])
        print("Smoke:", payload["smoke"])
        print("Signatures:")
        for name, sig in payload["signatures"].items():  # type: ignore[union-attr]
            print(f"  {name}: {sig}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
