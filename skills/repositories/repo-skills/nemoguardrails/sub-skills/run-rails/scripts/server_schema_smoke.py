#!/usr/bin/env python3
"""Deterministic server schema smoke for NeMo Guardrails.

This helper validates the OpenAI-compatible request normalization logic and
hits the shallow health/config discovery endpoints without contacting any live
provider.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import tempfile
import warnings
from pathlib import Path
from typing import Any, Optional


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    return parser


def _write_sample_config_tree(root: Path) -> None:
    sample = root / "sample"
    sample.mkdir(parents=True, exist_ok=True)
    (sample / "config.yml").write_text("models: []\n", encoding="utf-8")


def run_smoke() -> dict[str, Any]:
    os.environ.setdefault("NEMO_GUARDRAILS_DISABLE_CHAT_UI", "true")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        logging.getLogger("httpx").setLevel(logging.ERROR)
        try:
            from fastapi.testclient import TestClient
            from nemoguardrails.server import api
            from nemoguardrails.server.schemas.openai import GuardrailsChatCompletionRequest
        except ImportError as exc:  # pragma: no cover - exercised only in underspecified environments
            raise SystemExit(
                "Server dependencies are missing. Install the server extra before running this smoke."
            ) from exc

    request = GuardrailsChatCompletionRequest.model_validate(
        {
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": "Hello"}],
            "guardrails": {"config_id": "sample"},
        }
    )

    if request.guardrails.config_ids != ["sample"]:
        raise RuntimeError(f"config_id normalization failed: {request.guardrails.config_ids!r}")

    mixed_error = None
    try:
        GuardrailsChatCompletionRequest.model_validate(
            {
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": "Hello"}],
                "guardrails": {"config_id": "sample", "config_ids": ["sample", "other"]},
            }
        )
        raise RuntimeError("Expected config_id/config_ids exclusivity to fail")
    except Exception as exc:
        mixed_error = str(exc)

    state_error = None
    try:
        api._validate_public_state_shape({"version": "2.x"})
        raise RuntimeError("Expected Colang 2.0 HTTP state validation to fail")
    except Exception as exc:
        state_error = getattr(exc, "detail", str(exc))

    original_path = api.app.rails_config_path
    original_single_mode = api.app.single_config_mode
    original_single_id = api.app.single_config_id
    original_default_config_id = api.app.default_config_id

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        _write_sample_config_tree(root)

        try:
            api.app.rails_config_path = str(root)
            api.app.single_config_mode = False
            api.app.single_config_id = None
            api.app.default_config_id = None
            api.llm_rails_instances.clear()

            with TestClient(api.app) as client:
                health = client.get("/v1/health")
                configs = client.get("/v1/rails/configs")

            if health.status_code != 200:
                raise RuntimeError(f"Unexpected /v1/health status: {health.status_code}")
            if health.json() != {"status": "pass"}:
                raise RuntimeError(f"Unexpected /v1/health body: {health.json()!r}")

            if configs.status_code != 200:
                raise RuntimeError(f"Unexpected /v1/rails/configs status: {configs.status_code}")
            config_ids = [item["id"] for item in configs.json()]
            if config_ids != ["sample"]:
                raise RuntimeError(f"Unexpected /v1/rails/configs body: {config_ids!r}")

            return {
                "request_normalization": {
                    "config_id": request.guardrails.config_id,
                    "config_ids": request.guardrails.config_ids,
                    "exclusive_error": mixed_error,
                },
                "state_error": state_error,
                "health": health.json(),
                "config_ids": config_ids,
            }
        finally:
            api.app.rails_config_path = original_path
            api.app.single_config_mode = original_single_mode
            api.app.single_config_id = original_single_id
            api.app.default_config_id = original_default_config_id
            api.llm_rails_instances.clear()


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Request config_id normalized to: {result['request_normalization']['config_ids']}")
        print(f"State validation error: {result['state_error']}")
        print(f"/v1/health: {result['health']}")
        print(f"/v1/rails/configs: {result['config_ids']}")
        print("Schema smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
