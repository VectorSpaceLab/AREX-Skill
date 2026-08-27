#!/usr/bin/env python3
"""No-secret PyRIT converter and seed-model smoke helper."""
from __future__ import annotations

import argparse
import asyncio
import inspect
import json


async def run_conversion_smoke() -> dict[str, object]:
    from pyrit.converter import Base64Converter, SearchReplaceConverter
    from pyrit.models import SeedPrompt

    base64_result = await Base64Converter().convert_async(prompt="hello", input_type="text")
    replace_result = await SearchReplaceConverter(pattern="red", replace="blue").convert_async(prompt="red team", input_type="text")
    seed = SeedPrompt(value="Test {{ objective }}", parameters=["objective"], data_type="text")
    return {
        "Base64Converter.signature": str(inspect.signature(Base64Converter))[:500],
        "SearchReplaceConverter.signature": str(inspect.signature(SearchReplaceConverter))[:500],
        "SeedPrompt.signature": str(inspect.signature(SeedPrompt))[:500],
        "base64_output": getattr(base64_result, "output_text", None) or getattr(base64_result, "text", None) or str(base64_result),
        "search_replace_output": getattr(replace_result, "output_text", None) or getattr(replace_result, "text", None) or str(replace_result),
        "seed_parameters": seed.parameters,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run offline converter and seed-model checks without network or secrets.")
    parser.add_argument("--json", action="store_true", help="print JSON output")
    args = parser.parse_args()
    try:
        checks = asyncio.run(run_conversion_smoke())
        result = {"ok": True, "checks": checks}
    except Exception as exc:  # noqa: BLE001
        result = {"ok": False, "errors": [f"{type(exc).__name__}: {exc}"]}
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
