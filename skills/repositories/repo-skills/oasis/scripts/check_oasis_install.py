#!/usr/bin/env python3
"""Check that camel-oasis imports and expose the expected public API.

Examples:
    python check_oasis_install.py
    python check_oasis_install.py --json
    python check_oasis_install.py --check-torch
"""
from __future__ import annotations

import argparse
import importlib.metadata as metadata
import inspect
import json
import sys
from typing import Any

EXPECTED_EXPORTS = (
    "make",
    "Platform",
    "ActionType",
    "DefaultPlatformType",
    "ManualAction",
    "LLMAction",
    "AgentGraph",
    "SocialAgent",
    "UserInfo",
    "generate_reddit_agent_graph",
    "generate_twitter_agent_graph",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify camel-oasis importability and key public API signatures."
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--check-torch",
        action="store_true",
        help="Also report torch/CUDA availability if torch is installed.",
    )
    return parser


def collect(check_torch: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "distribution": None,
        "oasis_version": None,
        "exports": {},
        "signatures": {},
        "warnings": [],
        "torch": None,
    }

    try:
        result["distribution"] = metadata.version("camel-oasis")
    except metadata.PackageNotFoundError:
        result["warnings"].append("Distribution metadata for camel-oasis was not found.")

    try:
        import oasis  # type: ignore
    except Exception as exc:  # noqa: BLE001 - diagnostic script should explain imports.
        result["import_error"] = repr(exc)
        if "FastMCP" in str(exc) and "mcp.server" in str(exc):
            result["warnings"].append(
                "camel-ai 0.2.78 can fail with mcp>=2. Install a compatible mcp<2 release."
            )
        return result

    result["oasis_version"] = getattr(oasis, "__version__", None)
    missing = []
    for name in EXPECTED_EXPORTS:
        has_name = hasattr(oasis, name)
        result["exports"][name] = has_name
        if not has_name:
            missing.append(name)

    for label, obj in [
        ("make", getattr(oasis, "make", None)),
        ("AgentGraph.__init__", getattr(getattr(oasis, "AgentGraph", None), "__init__", None)),
        ("SocialAgent.__init__", getattr(getattr(oasis, "SocialAgent", None), "__init__", None)),
        ("Platform.__init__", getattr(getattr(oasis, "Platform", None), "__init__", None)),
    ]:
        if obj is not None:
            try:
                result["signatures"][label] = str(inspect.signature(obj))
            except (TypeError, ValueError) as exc:
                result["signatures"][label] = f"unavailable: {exc}"

    try:
        twitter = [action.name for action in oasis.ActionType.get_default_twitter_actions()]
        reddit = [action.name for action in oasis.ActionType.get_default_reddit_actions()]
        result["default_actions"] = {"twitter": twitter, "reddit": reddit}
    except Exception as exc:  # noqa: BLE001
        result["warnings"].append(f"Could not inspect default actions: {exc}")

    if check_torch:
        try:
            import torch  # type: ignore

            torch_info: dict[str, Any] = {
                "version": getattr(torch, "__version__", None),
                "cuda_version": getattr(torch.version, "cuda", None),
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            }
            if torch.cuda.is_available():
                torch_info["cuda_device_0"] = torch.cuda.get_device_name(0)
            result["torch"] = torch_info
        except Exception as exc:  # noqa: BLE001
            result["torch"] = {"error": repr(exc)}

    result["ok"] = not missing and "import_error" not in result
    return result


def print_human(result: dict[str, Any]) -> None:
    print("camel-oasis check")
    print(f"  ok: {result['ok']}")
    print(f"  distribution: {result.get('distribution')}")
    print(f"  oasis.__version__: {result.get('oasis_version')}")
    if "import_error" in result:
        print(f"  import_error: {result['import_error']}")
    print("  exports:")
    for name, present in result.get("exports", {}).items():
        print(f"    {name}: {'yes' if present else 'missing'}")
    if result.get("signatures"):
        print("  signatures:")
        for name, signature in result["signatures"].items():
            print(f"    {name}: {signature}")
    if result.get("default_actions"):
        print("  default_actions:")
        for platform, actions in result["default_actions"].items():
            print(f"    {platform}: {', '.join(actions)}")
    if result.get("torch") is not None:
        print("  torch:")
        for key, value in result["torch"].items():
            print(f"    {key}: {value}")
    if result.get("warnings"):
        print("  warnings:")
        for warning in result["warnings"]:
            print(f"    - {warning}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = collect(check_torch=args.check_torch)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_human(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
