#!/usr/bin/env python3
"""Check a ChatterBot runtime without depending on a source checkout.

Examples:
  python scripts/check_chatterbot_environment.py --check-spacy-model en_core_web_sm
  python scripts/check_chatterbot_environment.py --instantiate --json
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import sys
from typing import Any


OPTIONAL_MODULES = {
    "pint": "pint",
    "pyyaml": "yaml",
    "chatterbot-corpus": "chatterbot_corpus",
    "django": "django",
    "pymongo": "pymongo",
    "redis": "redis",
    "langchain-redis": "langchain_redis",
    "langchain-huggingface": "langchain_huggingface",
    "ollama": "ollama",
    "openai": "openai",
}


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, "__version__", None)
        return {"ok": True, "version": version}
    except Exception as exc:  # diagnostic tool: preserve exception class/message
        return {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ChatterBot imports, metadata, spaCy models, and optional dependencies.")
    parser.add_argument("--check-spacy-model", action="append", default=[], help="spaCy model name to load, e.g. en_core_web_sm. May be repeated.")
    parser.add_argument("--optional", choices=sorted(OPTIONAL_MODULES), action="append", help="Optional dependency group/module to check. Omit to check common optionals.")
    parser.add_argument("--instantiate", action="store_true", help="Instantiate ChatBot with an in-memory SQL database and call get_response('Hello').")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    args = parser.parse_args()

    report: dict[str, Any] = {"python": sys.version.split()[0], "checks": {}}
    exit_code = 0

    try:
        import chatterbot
        from chatterbot import ChatBot
        version = importlib.metadata.version("ChatterBot")
        report["checks"]["chatterbot"] = {"ok": True, "version": version, "module_version": getattr(chatterbot, "__version__", None), "chatbot_class": str(ChatBot)}
    except Exception as exc:
        report["checks"]["chatterbot"] = {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}
        exit_code = 1
        ChatBot = None  # type: ignore[assignment]

    optionals = args.optional or sorted(OPTIONAL_MODULES)
    report["checks"]["optional_modules"] = {name: import_status(OPTIONAL_MODULES[name]) for name in optionals}

    if args.check_spacy_model:
        model_results = {}
        try:
            import spacy
            for model_name in args.check_spacy_model:
                try:
                    nlp = spacy.load(model_name)
                    model_results[model_name] = {"ok": True, "pipeline": list(nlp.pipe_names)}
                except Exception as exc:
                    model_results[model_name] = {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}
                    exit_code = 1
        except Exception as exc:
            for model_name in args.check_spacy_model:
                model_results[model_name] = {"ok": False, "error": f"spaCy import failed: {exc.__class__.__name__}: {exc}"}
                exit_code = 1
        report["checks"]["spacy_models"] = model_results

    if args.instantiate:
        if ChatBot is None:
            report["checks"]["instantiate"] = {"ok": False, "error": "ChatterBot import failed"}
            exit_code = 1
        else:
            try:
                bot = ChatBot("Diagnostic", database_uri=None, read_only=True)
                response = bot.get_response("Hello")
                report["checks"]["instantiate"] = {"ok": True, "response_text": str(response), "confidence": getattr(response, "confidence", None)}
            except Exception as exc:
                report["checks"]["instantiate"] = {"ok": False, "error": f"{exc.__class__.__name__}: {exc}"}
                exit_code = 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("ChatterBot environment diagnostic")
        print(json.dumps(report, indent=2, sort_keys=True))
        if exit_code:
            print("One or more required checks failed. See error fields above.", file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
