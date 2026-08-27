#!/usr/bin/env python3
from __future__ import annotations

import argparse
import inspect
import os
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from importlib import import_module
from typing import Literal

CheckName = Literal["import", "signature", "mock"]


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def load_litellm():
    return import_module("litellm")


def result_line(result: CheckResult) -> str:
    status = "ok" if result.ok else "fail"
    return f"{status}: {result.name}: {result.detail}"


def check_import() -> CheckResult:
    try:
        litellm = load_litellm()
    except Exception as exc:
        return CheckResult("import", False, f"could not import litellm: {exc}")

    version = getattr(litellm, "__version__", "unknown")
    required_attrs = ("completion", "acompletion", "embedding", "aembedding", "text_completion")
    missing = tuple(attr for attr in required_attrs if not hasattr(litellm, attr))
    if missing:
        return CheckResult("import", False, f"missing attributes: {', '.join(missing)}")
    return CheckResult("import", True, f"litellm imported; version={version}")


def missing_params(function, expected: Iterable[str]) -> tuple[str, ...]:
    signature = inspect.signature(function)
    params = signature.parameters
    has_kwargs = any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values())
    return tuple(name for name in expected if name not in params and not has_kwargs)


def check_signature() -> CheckResult:
    try:
        litellm = load_litellm()
    except Exception as exc:
        return CheckResult("signature", False, f"could not import litellm: {exc}")

    expectations = (
        (
            "completion",
            litellm.completion,
            (
                "model",
                "messages",
                "timeout",
                "temperature",
                "stream",
                "stream_options",
                "max_tokens",
                "max_completion_tokens",
                "response_format",
                "tools",
                "tool_choice",
                "base_url",
                "api_version",
                "api_key",
                "model_list",
                "extra_headers",
                "thinking",
                "web_search_options",
                "enable_json_schema_validation",
            ),
        ),
        (
            "acompletion",
            litellm.acompletion,
            (
                "model",
                "messages",
                "timeout",
                "temperature",
                "stream",
                "stream_options",
                "max_tokens",
                "max_completion_tokens",
                "response_format",
                "tools",
                "tool_choice",
                "base_url",
                "api_version",
                "api_key",
                "model_list",
                "extra_headers",
                "thinking",
                "web_search_options",
                "enable_json_schema_validation",
            ),
        ),
        (
            "embedding",
            litellm.embedding,
            (
                "model",
                "input",
                "dimensions",
                "encoding_format",
                "timeout",
                "api_base",
                "api_version",
                "api_key",
                "caching",
                "user",
            ),
        ),
    )

    failures = tuple(
        f"{name} missing {', '.join(missing)}"
        for name, function, expected in expectations
        if (missing := missing_params(function, expected))
    )
    if failures:
        return CheckResult("signature", False, "; ".join(failures))
    return CheckResult("signature", True, "core SDK signatures include expected parameters")


def read_content(response) -> str:
    return response.choices[0].message.content


def check_mock() -> CheckResult:
    try:
        litellm = load_litellm()
        response = litellm.completion(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": "Return the smoke token."}],
            mock_response="sdk-smoke-ok",
        )
    except Exception as exc:
        return CheckResult("mock", False, f"mock completion failed: {exc}")

    content = read_content(response)
    if content != "sdk-smoke-ok":
        return CheckResult("mock", False, f"unexpected mock content: {content!r}")
    return CheckResult("mock", True, "mock completion returned expected content")


def run_provider_smoke(model: str, api_key_env: str, timeout: float) -> CheckResult:
    api_key = os.environ.get(api_key_env)
    if not api_key:
        return CheckResult(
            "provider-smoke",
            False,
            f"environment variable {api_key_env} is not set",
        )

    try:
        litellm = load_litellm()
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": "Reply with exactly: sdk-smoke-ok"}],
            api_key=api_key,
            timeout=timeout,
            temperature=0,
            max_tokens=12,
        )
    except Exception as exc:
        return CheckResult("provider-smoke", False, f"live provider call failed: {exc}")

    content = read_content(response)
    if not content:
        return CheckResult("provider-smoke", False, "provider returned empty content")
    return CheckResult("provider-smoke", True, f"provider returned content: {content[:80]!r}")


def parse_checks(raw_checks: list[str]) -> tuple[CheckName, ...]:
    if "all" in raw_checks:
        return ("import", "signature", "mock")
    ordered = tuple(dict.fromkeys(raw_checks))
    return tuple(check for check in ordered if check in {"import", "signature", "mock"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safe LiteLLM SDK smoke checks. No live provider call runs unless --provider-smoke is set with --model and --api-key-env.",
    )
    parser.add_argument(
        "--checks",
        nargs="+",
        default=["all"],
        choices=("all", "import", "signature", "mock"),
        help="Local no-network checks to run.",
    )
    parser.add_argument(
        "--provider-smoke",
        action="store_true",
        help="Run one optional live completion call. Requires --model and --api-key-env.",
    )
    parser.add_argument("--model", help="Model for optional provider smoke, for example openai/gpt-4o-mini.")
    parser.add_argument("--api-key-env", help="Environment variable containing the provider API key.")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout in seconds for optional provider smoke.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    checks = parse_checks(args.checks)
    check_functions = {
        "import": check_import,
        "signature": check_signature,
        "mock": check_mock,
    }

    results = [check_functions[check]() for check in checks]

    if args.provider_smoke:
        if not args.model or not args.api_key_env:
            results.append(
                CheckResult(
                    "provider-smoke",
                    False,
                    "--provider-smoke requires --model and --api-key-env",
                )
            )
        else:
            results.append(run_provider_smoke(args.model, args.api_key_env, args.timeout))

    for result in results:
        print(result_line(result))

    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
