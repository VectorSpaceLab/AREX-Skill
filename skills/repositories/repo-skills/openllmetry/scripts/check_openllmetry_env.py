#!/usr/bin/env python3
"""Check an installed OpenLLMetry Python environment without provider calls.

The script verifies distribution metadata and safe imports for the SDK,
semantic-convention package, and representative instrumentation modules. It
never calls a provider API, opens network connections, or imports checkout
paths unless the caller's Python environment already exposes them.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass, asdict
from importlib import metadata
from typing import Any

CORE_DISTRIBUTIONS = [
    "traceloop-sdk",
    "opentelemetry-semantic-conventions-ai",
]

INSTRUMENTATION_DISTRIBUTIONS = [
    "opentelemetry-instrumentation-agno",
    "opentelemetry-instrumentation-alephalpha",
    "opentelemetry-instrumentation-anthropic",
    "opentelemetry-instrumentation-bedrock",
    "opentelemetry-instrumentation-chromadb",
    "opentelemetry-instrumentation-cohere",
    "opentelemetry-instrumentation-crewai",
    "opentelemetry-instrumentation-google-generativeai",
    "opentelemetry-instrumentation-groq",
    "opentelemetry-instrumentation-haystack",
    "opentelemetry-instrumentation-lancedb",
    "opentelemetry-instrumentation-langchain",
    "opentelemetry-instrumentation-litellm",
    "opentelemetry-instrumentation-llamaindex",
    "opentelemetry-instrumentation-marqo",
    "opentelemetry-instrumentation-mcp",
    "opentelemetry-instrumentation-milvus",
    "opentelemetry-instrumentation-mistralai",
    "opentelemetry-instrumentation-ollama",
    "opentelemetry-instrumentation-openai",
    "opentelemetry-instrumentation-openai-agents",
    "opentelemetry-instrumentation-pinecone",
    "opentelemetry-instrumentation-qdrant",
    "opentelemetry-instrumentation-replicate",
    "opentelemetry-instrumentation-sagemaker",
    "opentelemetry-instrumentation-together",
    "opentelemetry-instrumentation-transformers",
    "opentelemetry-instrumentation-vertexai",
    "opentelemetry-instrumentation-voyageai",
    "opentelemetry-instrumentation-watsonx",
    "opentelemetry-instrumentation-weaviate",
    "opentelemetry-instrumentation-writer",
]

SAFE_IMPORTS = [
    "traceloop.sdk",
    "traceloop.sdk.decorators",
    "traceloop.sdk.tracing.manual",
    "opentelemetry.semconv_ai",
]

REPRESENTATIVE_INSTRUMENTOR_IMPORTS = [
    "opentelemetry.instrumentation.openai",
    "opentelemetry.instrumentation.anthropic",
    "opentelemetry.instrumentation.langchain",
    "opentelemetry.instrumentation.mcp",
    "opentelemetry.instrumentation.crewai",
    "opentelemetry.instrumentation.ollama",
    "opentelemetry.instrumentation.voyageai",
    "opentelemetry.instrumentation.weaviate",
]

OPTIONAL_INSTRUMENTOR_IMPORTS = [
    "opentelemetry.instrumentation.bedrock",
    "opentelemetry.instrumentation.chromadb",
    "opentelemetry.instrumentation.google_generativeai",
    "opentelemetry.instrumentation.groq",
    "opentelemetry.instrumentation.lancedb",
    "opentelemetry.instrumentation.llamaindex",
    "opentelemetry.instrumentation.marqo",
    "opentelemetry.instrumentation.milvus",
    "opentelemetry.instrumentation.mistralai",
    "opentelemetry.instrumentation.pinecone",
    "opentelemetry.instrumentation.qdrant",
    "opentelemetry.instrumentation.replicate",
    "opentelemetry.instrumentation.sagemaker",
    "opentelemetry.instrumentation.together",
    "opentelemetry.instrumentation.transformers",
    "opentelemetry.instrumentation.vertexai",
    "opentelemetry.instrumentation.writer",
]


@dataclass(slots=True)
class DistributionCheck:
    name: str
    installed: bool
    version: str | None = None
    entry_points: dict[str, str] | None = None
    error: str | None = None


@dataclass(slots=True)
class ImportCheck:
    module: str
    ok: bool
    error: str | None = None


def check_distribution(name: str) -> DistributionCheck:
    try:
        dist = metadata.distribution(name)
    except metadata.PackageNotFoundError as exc:
        return DistributionCheck(name=name, installed=False, error=str(exc))
    entry_points = {
        ep.name: ep.value
        for ep in dist.entry_points
        if ep.group == "opentelemetry_instrumentor"
    }
    return DistributionCheck(
        name=name,
        installed=True,
        version=dist.version,
        entry_points=entry_points or None,
    )


def check_import(module: str) -> ImportCheck:
    try:
        importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001 - this is a diagnostic tool
        return ImportCheck(module=module, ok=False, error=f"{type(exc).__name__}: {exc}")
    return ImportCheck(module=module, ok=True)


def build_report(include_optional_imports: bool) -> dict[str, Any]:
    distribution_names = CORE_DISTRIBUTIONS + INSTRUMENTATION_DISTRIBUTIONS
    import_names = SAFE_IMPORTS + REPRESENTATIVE_INSTRUMENTOR_IMPORTS
    if include_optional_imports:
        import_names += OPTIONAL_INSTRUMENTOR_IMPORTS

    distributions = [check_distribution(name) for name in distribution_names]
    imports = [check_import(name) for name in import_names]
    required_imports_ok = all(item.ok for item in imports if item.module in SAFE_IMPORTS)

    return {
        "python": sys.version.split()[0],
        "summary": {
            "distributions_checked": len(distributions),
            "distributions_installed": sum(item.installed for item in distributions),
            "imports_checked": len(imports),
            "imports_ok": sum(item.ok for item in imports),
            "safe_imports_ok": required_imports_ok,
        },
        "distributions": [asdict(item) for item in distributions],
        "imports": [asdict(item) for item in imports],
        "notes": [
            "Optional instrumentor imports can fail when the target client library is not installed.",
            "This checker does not call provider APIs or validate live cloud/vector/local services.",
        ],
    }


def print_text(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print(
        "OpenLLMetry environment: "
        f"{summary['distributions_installed']}/{summary['distributions_checked']} distributions installed; "
        f"{summary['imports_ok']}/{summary['imports_checked']} imports ok"
    )
    print(f"Python: {report['python']}")
    print()
    for item in report["distributions"]:
        status = item["version"] if item["installed"] else f"missing ({item['error']})"
        print(f"{item['name']}: {status}")
    print()
    for item in report["imports"]:
        if item["ok"]:
            print(f"import ok: {item['module']}")
        else:
            print(f"import failed: {item['module']} -> {item['error']}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check installed OpenLLMetry metadata and safe imports without provider calls.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument(
        "--include-optional-imports",
        action="store_true",
        help="Also try instrumentor modules that often require optional target client packages",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    report = build_report(include_optional_imports=args.include_optional_imports)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report["summary"]["safe_imports_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
