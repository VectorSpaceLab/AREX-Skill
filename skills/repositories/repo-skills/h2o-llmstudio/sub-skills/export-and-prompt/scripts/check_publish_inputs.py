#!/usr/bin/env python3
"""Safely preflight Hugging Face export inputs without publishing anything."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from check_experiment_artifacts import (  # noqa: E402
    device_check,
    load_yaml_mapping,
    normalize_hf_repo_name,
)

MODEL_CARD_TEMPLATE_MAP = {
    "text_causal_language_modeling": (
        "text_causal_language_modeling_model_card_template.md",
        "text_causal_language_modeling_experiment_summary_card_template.md",
    ),
    "text_causal_classification_modeling": (
        "text_causal_classification_model_card_template.md",
        "text_causal_classification_experiment_summary_card_template.md",
    ),
    "text_causal_regression_modeling": (
        "text_causal_regression_model_card_template.md",
        "text_causal_regression_experiment_summary_card_template.md",
    ),
    "text_sequence_to_sequence_modeling": (
        "text_sequence_to_sequence_modeling_model_card_template.md",
        "text_sequence_to_sequence_modeling_experiment_summary_card_template.md",
    ),
}


def parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "f", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"invalid boolean value: {value!r}")


def expected_templates(problem_type: str) -> tuple[str | None, str | None]:
    return MODEL_CARD_TEMPLATE_MAP.get(problem_type, (None, None))


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preflight local inputs before publishing a trained experiment to Hugging Face Hub.",
    )
    parser.add_argument(
        "-p",
        "--path_to_experiment",
        required=True,
        help="Experiment output directory to inspect",
    )
    parser.add_argument(
        "-d",
        "--device",
        default="cuda:0",
        help="Device string to validate",
    )
    parser.add_argument(
        "-a",
        "--api_key",
        default=os.getenv("HF_TOKEN", ""),
        help="Hugging Face write token",
    )
    parser.add_argument(
        "-u",
        "--user_id",
        default="",
        help="Hugging Face account name",
    )
    parser.add_argument(
        "-m",
        "--model_name",
        default="",
        help="Target Hugging Face model name",
    )
    parser.add_argument(
        "-s",
        "--safe_serialization",
        type=parse_bool,
        default=True,
        help="Whether to use safe serialization during export",
    )
    parser.add_argument(
        "--check-network",
        action="store_true",
        help="Perform a lightweight Hugging Face auth/network probe",
    )
    parser.add_argument(
        "--require-auth",
        action="store_true",
        help="Fail when no API token is supplied and no login probe is requested",
    )
    parser.add_argument(
        "--model-cards-dir",
        default="model_cards",
        help="Directory that should contain the model-card templates",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as failures",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    experiment_dir = Path(args.path_to_experiment).expanduser()
    model_cards_dir = Path(args.model_cards_dir).expanduser()

    ok_count = 0
    warn_count = 0
    fail_count = 0

    def ok(message: str) -> None:
        nonlocal ok_count
        ok_count += 1
        print(f"[OK] {message}")

    def warn(message: str) -> None:
        nonlocal warn_count
        warn_count += 1
        print(f"[WARN] {message}")

    def fail(message: str) -> None:
        nonlocal fail_count
        fail_count += 1
        print(f"[FAIL] {message}")

    if not experiment_dir.exists():
        fail(f"experiment directory not found: {experiment_dir}")
        return 1
    if not experiment_dir.is_dir():
        fail(f"experiment path is not a directory: {experiment_dir}")
        return 1
    ok(f"experiment directory: {experiment_dir}")

    cfg_path = experiment_dir / "cfg.yaml"
    checkpoint_path = experiment_dir / "checkpoint.pth"
    if not cfg_path.exists():
        fail("cfg.yaml is missing")
        return 1
    if not checkpoint_path.exists():
        fail("checkpoint.pth is missing")
        return 1

    ok("cfg.yaml is present")
    ok("checkpoint.pth is present")

    try:
        cfg: dict[str, Any] = load_yaml_mapping(cfg_path)
        ok("cfg.yaml parsed successfully")
    except Exception as exc:
        fail(f"cfg.yaml could not be parsed: {exc}")
        return 1

    problem_type = str(cfg.get("problem_type", "")).strip()
    if not problem_type:
        fail("problem_type is missing from cfg.yaml")
        return 1

    if problem_type in MODEL_CARD_TEMPLATE_MAP:
        ok(f"problem type is supported for export: {problem_type}")
    else:
        fail(f"unsupported problem type for export: {problem_type}")
        return 1

    card_template, summary_template = expected_templates(problem_type)
    assert card_template is not None and summary_template is not None

    if model_cards_dir.exists() and model_cards_dir.is_dir():
        ok(f"model-card template directory is available: {model_cards_dir}")
    else:
        fail(f"model-card template directory is missing: {model_cards_dir}")

    for template_name in (card_template, summary_template):
        template_path = model_cards_dir / template_name
        if template_path.exists():
            ok(f"template found: {template_path}")
        else:
            fail(f"template is missing: {template_path}")

    valid, message = device_check(args.device)
    if valid:
        ok(message)
    else:
        fail(message)

    output_directory_value = cfg.get("output_directory")
    if not output_directory_value:
        fail("cfg.output_directory is missing from cfg.yaml")
    else:
        output_directory = Path(str(output_directory_value)).expanduser()
        if output_directory.exists() and output_directory.is_dir():
            if os.access(output_directory, os.W_OK):
                ok(f"cfg.output_directory is writable: {output_directory}")
            else:
                fail(f"cfg.output_directory is not writable: {output_directory}")
        else:
            fail(f"cfg.output_directory does not exist: {output_directory}")

        if output_directory.resolve() != experiment_dir.resolve():
            warn(
                "cfg.output_directory differs from the inspected experiment directory; "
                "the exporter writes hf.yaml to the configured output directory"
            )

    api_key = str(args.api_key or "").strip()
    auth_confirmed = False
    if api_key:
        ok("a Hugging Face API token was supplied")
        auth_confirmed = True
    else:
        warn(
            "no Hugging Face API token was supplied; publishing will depend on an existing login"
        )

    if args.check_network:
        try:
            import huggingface_hub
        except Exception as exc:
            fail(f"cannot probe Hugging Face auth/network because huggingface_hub is unavailable: {exc}")
        else:
            try:
                api = huggingface_hub.HfApi()
                if api_key:
                    whoami = api.whoami(token=api_key)
                else:
                    whoami = api.whoami()
                user_name = whoami.get("name", "<unknown>") if isinstance(whoami, dict) else str(whoami)
                ok(f"Hugging Face whoami succeeded for user: {user_name}")
                auth_confirmed = True
            except Exception as exc:
                fail(f"Hugging Face auth/network probe failed: {exc}")
    elif args.require_auth and not auth_confirmed:
        fail("authentication was required but no API token was supplied and no login probe was requested")

    if not args.safe_serialization:
        warn("safe serialization is disabled for this preflight")
    else:
        ok("safe serialization is enabled")

    hf_transfer_enabled = os.getenv("HF_HUB_ENABLE_HF_TRANSFER", "1").strip().lower()
    if hf_transfer_enabled in {"0", "false", "off", "no"}:
        warn("HF transfer acceleration is disabled in the environment")
    else:
        ok("HF transfer acceleration is enabled or left at its default")

    model_name = str(args.model_name or experiment_dir.name).strip()
    normalized_model_name = normalize_hf_repo_name(model_name)
    if normalized_model_name:
        ok(f"normalized model name: {normalized_model_name}")
    else:
        fail("model_name becomes empty after normalization")

    repo_user = str(args.user_id or "").strip()
    if repo_user:
        ok(f"target account name supplied: {repo_user}")
        repo_id = f"{repo_user}/{normalized_model_name}"
    else:
        warn(
            "no account name was supplied; the runtime will resolve the logged-in account if available"
        )
        repo_id = f"<logged-in-user>/{normalized_model_name}"

    ok(f"target repository id preview: {repo_id}")

    found_optional = [
        name
        for name in (
            "classification_head.pth",
            "regression_head.pth",
            "adapter_model",
        )
        if (experiment_dir / name).exists()
    ]
    if found_optional:
        ok("optional export artifacts present: " + ", ".join(found_optional))

    print(
        f"Summary: {ok_count} ok, {warn_count} warning(s), {fail_count} failure(s)"
    )

    if fail_count:
        return 1
    if args.strict and warn_count:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
