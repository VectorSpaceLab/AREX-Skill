#!/usr/bin/env python3
"""Preflight and optionally run a tiny LangExtract Ollama extraction demo.

Examples:
  python ollama_demo.py --preflight-only
  python ollama_demo.py --model gemma2:2b --url http://localhost:11434 --run

The default mode performs only local service/model checks. Add --run to call
`lx.extract()` against the Ollama service. The script never downloads models or
starts services; pull models and start Ollama outside this helper.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any

DEFAULT_URL = "http://localhost:11434"
DEFAULT_MODEL = "gemma2:2b"


def _get_json(url: str, timeout: float) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw or "{}")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not connect to Ollama at {url}: {exc}") from exc
    except TimeoutError as exc:
        raise RuntimeError(f"Timed out connecting to Ollama at {url}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Ollama endpoint returned non-JSON at {url}: {exc}") from exc


def _list_models(base_url: str, timeout: float) -> list[str]:
    endpoint = base_url.rstrip("/") + "/api/tags"
    payload = _get_json(endpoint, timeout)
    models = payload.get("models") or []
    names: list[str] = []
    for item in models:
        if isinstance(item, dict):
            name = item.get("name") or item.get("model")
            if isinstance(name, str):
                names.append(name)
    return sorted(names)


def _model_available(model: str, models: list[str]) -> bool:
    if model in models:
        return True
    base = model.split(":", 1)[0]
    return any(name == base or name.startswith(base + ":") for name in models)


def _import_langextract() -> Any:
    try:
        import langextract as lx  # pylint: disable=import-outside-toplevel
    except Exception as exc:  # pragma: no cover - user diagnostic path
        raise SystemExit(
            "Could not import langextract in this Python environment. Install "
            f"the package before running --run. Original error: {exc}"
        ) from exc
    return lx


def _run_demo(args: argparse.Namespace) -> None:
    lx = _import_langextract()
    examples = [
        lx.data.ExampleData(
            text="J.R.R. Tolkien was an English writer, best known for high-fantasy.",
            extractions=[
                lx.data.Extraction(
                    extraction_class="author_details",
                    extraction_text="J.R.R. Tolkien",
                    attributes={"genre": "high-fantasy"},
                )
            ],
        )
    ]
    result = lx.extract(
        text_or_documents="Isaac Asimov was a prolific science fiction writer.",
        prompt_description="Extract the author's full name and their primary literary genre.",
        examples=examples,
        model_id=args.model,
        model_url=args.url,
        temperature=args.temperature,
        timeout=args.inference_timeout,
        fence_output=False,
        use_schema_constraints=False,
        max_workers=1,
        batch_length=1,
        show_progress=False,
    )
    print("Extraction result:")
    for extraction in result.extractions or []:
        print(f"- {extraction.extraction_class}: {extraction.extraction_text} {extraction.attributes or {}}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preflight a local Ollama service and optionally run a tiny LangExtract demo."
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="Ollama base URL.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name to check/use.")
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Only check service/model availability. This is the default unless --run is passed.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Actually call lx.extract() through Ollama after preflight succeeds.",
    )
    parser.add_argument("--timeout", type=float, default=2.0, help="HTTP timeout for service preflight.")
    parser.add_argument("--inference-timeout", type=int, default=120, help="Timeout passed to the Ollama provider for --run.")
    parser.add_argument("--temperature", type=float, default=0.1)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        models = _list_models(args.url, args.timeout)
    except RuntimeError as exc:
        print(f"Ollama preflight failed: {exc}", file=sys.stderr)
        print("Start Ollama and pull a model before running live extraction.", file=sys.stderr)
        return 1

    print(f"Ollama service reachable at {args.url}")
    if models:
        print("Installed models:")
        for model in models:
            print(f"  - {model}")
    else:
        print("No installed Ollama models were reported.")

    if not _model_available(args.model, models):
        print(
            f"Requested model {args.model!r} was not found. Pull it before running: ollama pull {args.model}",
            file=sys.stderr,
        )
        return 1 if args.run else 0

    print(f"Requested model {args.model!r} appears available.")
    if not args.run:
        print("Preflight complete. Add --run to call lx.extract() through Ollama.")
        return 0

    _run_demo(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
