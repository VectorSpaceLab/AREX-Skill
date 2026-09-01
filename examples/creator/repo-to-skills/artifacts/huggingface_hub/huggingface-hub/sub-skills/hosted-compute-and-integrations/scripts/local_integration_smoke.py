#!/usr/bin/env python3
"""Run a local-only hosted-integration smoke fixture.

This helper creates a tiny PyTorchModelHubMixin model and card, writes and
reloads sharded safetensors, stores the state dict in DDUF, and exercises a
mocked Space/webhook configuration recovery. It blocks socket connections and
never reads a token or mutates a Hub resource.

Examples:
    python scripts/local_integration_smoke.py
    python scripts/local_integration_smoke.py --work-dir ./local-smoke --json
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import socket
import tempfile
import warnings
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from typing import Any, Iterator
from unittest.mock import create_autospec, patch


INSTALL_HINTS = {
    "oauth": "Install the huggingface_hub OAuth extra (authlib and session dependencies).",
    "gradio": "Install the huggingface_hub Gradio extra to use WebhooksServer.",
    "torch": "Install the huggingface_hub torch extra and a backend-compatible torch build.",
    "safetensors": "Install safetensors for safe checkpoint and mixin serialization.",
    "tensorboard": "Install tensorboard or tensorboardX before using HFSummaryWriter.",
}
MODULE_GROUPS = {
    "oauth": ("authlib", "fastapi", "starlette"),
    "gradio": ("gradio", "fastapi"),
    "torch": ("torch",),
    "safetensors": ("safetensors",),
    "tensorboard": ("tensorboard", "tensorboardX"),
}


def diagnose_optional_dependencies() -> dict[str, dict[str, Any]]:
    """Return actionable optional-dependency status without importing modules."""
    report: dict[str, dict[str, Any]] = {}
    for feature, modules in MODULE_GROUPS.items():
        available = {module: importlib.util.find_spec(module) is not None for module in modules}
        if feature == "tensorboard":
            ok = any(available.values())
        else:
            ok = all(available.values())
        report[feature] = {
            "ok": ok,
            "modules": available,
            "install": INSTALL_HINTS[feature],
        }
    return report


@contextmanager
def block_network() -> Iterator[None]:
    """Fail the fixture if package code attempts an outbound socket connection."""
    with patch.object(
        socket.socket,
        "connect",
        side_effect=AssertionError("network access is forbidden in this smoke"),
    ):
        yield


def validate_space_webhook_config(config: dict[str, str]) -> None:
    """Validate the small synthetic config before any mocked client mutation."""
    errors: list[str] = []
    secret = config.get("WEBHOOK_SECRET", "")
    model_id = config.get("MODEL_ID", "")
    if len(secret) < 16 or secret.lower().startswith("invalid"):
        errors.append("WEBHOOK_SECRET must be a non-placeholder value of at least 16 characters")
    if model_id.count("/") != 1 or any(part.strip() == "" for part in model_id.split("/")):
        errors.append("MODEL_ID must be an OWNER/REPOSITORY identifier")
    if errors:
        raise ValueError("; ".join(errors))


def run_fixture(root: Path) -> dict[str, Any]:
    """Execute all local and mocked stages and return assertion evidence."""
    diagnostics = diagnose_optional_dependencies()
    assert set(diagnostics) == {"oauth", "gradio", "torch", "safetensors", "tensorboard"}
    assert all("ok" in status and "modules" in status and "install" in status for status in diagnostics.values())
    for required in ("torch", "safetensors"):
        if not diagnostics[required]["ok"]:
            raise RuntimeError(diagnostics[required]["install"])

    import safetensors.torch
    import torch
    import torch.nn as nn
    from huggingface_hub import (
        HfApi,
        ModelCard,
        ModelHubMixin,
        PyTorchModelHubMixin,
        SpaceRuntime,
        WebhooksServer,
        export_entries_as_dduf,
        load_torch_model,
        read_dduf_file,
        save_torch_state_dict,
    )

    class TinyModel(
        nn.Module,
        PyTorchModelHubMixin,
        library_name="local-tiny-model",
        license="apache-2.0",
        pipeline_tag="feature-extraction",
        tags=["local-only"],
    ):
        def __init__(self, width: int = 4) -> None:
            super().__init__()
            self.width = width
            self.projection = nn.Linear(width, width)

        def forward(self, inputs: torch.Tensor) -> torch.Tensor:
            return self.projection(inputs)

    assert issubclass(TinyModel, ModelHubMixin)
    root.mkdir(parents=True, exist_ok=True)
    model_dir = root / "mixin-model"
    shard_dir = root / "shards"
    shard_dir.mkdir(parents=True, exist_ok=True)
    dduf_path = root / "tiny.dduf"

    torch.manual_seed(7)
    model = TinyModel(width=4)
    expected = {key: value.detach().clone() for key, value in model.state_dict().items()}
    captured_local_messages = io.StringIO()

    # ModelHubMixin/PyTorchModelHubMixin + generated card round trip.
    model.save_pretrained(model_dir)
    assert {"README.md", "config.json", "model.safetensors"}.issubset(
        path.name for path in model_dir.iterdir()
    )
    config = json.loads((model_dir / "config.json").read_text(encoding="utf-8"))
    assert config == {"width": 4}
    card = ModelCard.load(model_dir / "README.md")
    assert card.data.library_name == "local-tiny-model"
    assert card.data.license == "apache-2.0"
    assert {"local-only", "model_hub_mixin", "pytorch_model_hub_mixin"}.issubset(card.data.tags)
    with redirect_stdout(captured_local_messages):
        restored_mixin = TinyModel.from_pretrained(model_dir)
    assert restored_mixin.width == 4 and not restored_mixin.training
    for key, value in expected.items():
        assert torch.equal(restored_mixin.state_dict()[key], value)

    # Force multiple local safetensors shards and validate generated index/load.
    save_torch_state_dict(expected, shard_dir, max_shard_size=32, safe_serialization=True)
    index_path = shard_dir / "model.safetensors.index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert set(index["weight_map"]) == set(expected)
    assert len(set(index["weight_map"].values())) >= 2
    for shard_name in index["weight_map"].values():
        shard_path = Path(shard_name)
        assert not shard_path.is_absolute() and ".." not in shard_path.parts
        assert shard_path.suffix == ".safetensors" and (shard_dir / shard_path).is_file()
    restored_shards = TinyModel(width=4)
    # Each shard contains only part of the model, so the loader must use
    # non-strict per-shard loads; its final aggregate result still proves that
    # the complete index covers exactly the model keys.
    incompatible = load_torch_model(restored_shards, shard_dir, strict=False, safe=True, map_location="cpu")
    assert incompatible.missing_keys == [] and incompatible.unexpected_keys == []
    for key, value in expected.items():
        assert torch.equal(restored_shards.state_dict()[key], value)

    # DDUF round trip: top-level safetensors bytes plus required model index.
    tensor_bytes = safetensors.torch.save(expected)
    export_entries_as_dduf(
        dduf_path,
        [
            ("model_index.json", json.dumps({"_class_name": "TinyModel", "width": 4}).encode()),
            ("model.safetensors", tensor_bytes),
        ],
    )
    entries = read_dduf_file(dduf_path)
    dduf_index = json.loads(entries["model_index.json"].read_text())
    assert dduf_index == {"_class_name": "TinyModel", "width": 4}
    with entries["model.safetensors"].as_mmap() as mm:
        restored_dduf = safetensors.torch.load(mm)
    assert set(restored_dduf) == set(expected)
    for key, value in expected.items():
        assert torch.equal(restored_dduf[key], value)

    # Mocked lifecycle: invalid config is rejected before any client mutation;
    # correction plans Space secret/variable + webhook registration in mocks only.
    api = create_autospec(HfApi, instance=True)
    invalid = {"WEBHOOK_SECRET": "invalid", "MODEL_ID": "missing-owner"}
    try:
        validate_space_webhook_config(invalid)
    except ValueError as error:
        invalid_error = str(error)
        assert "WEBHOOK_SECRET" in invalid_error and "MODEL_ID" in invalid_error
    else:
        raise AssertionError("invalid Space/webhook configuration was accepted")
    api.add_space_secret.assert_not_called()
    api.add_space_variable.assert_not_called()
    api.create_webhook.assert_not_called()

    corrected = {
        "WEBHOOK_SECRET": "local-test-secret-42",
        "MODEL_ID": "local/tiny-model",
    }
    validate_space_webhook_config(corrected)
    api.get_space_runtime.side_effect = [
        SpaceRuntime({"stage": "CONFIG_ERROR", "hardware": {"current": "cpu-basic"}}),
        SpaceRuntime({"stage": "RUNNING", "hardware": {"current": "cpu-basic"}}),
    ]
    before = api.get_space_runtime("local/synthetic-space", token=False)
    assert before.stage == "CONFIG_ERROR"
    api.add_space_secret(
        "local/synthetic-space", "WEBHOOK_SECRET", corrected["WEBHOOK_SECRET"], token=False
    )
    api.add_space_variable("local/synthetic-space", "MODEL_ID", corrected["MODEL_ID"], token=False)
    after = api.get_space_runtime("local/synthetic-space", token=False)
    assert after.stage == "RUNNING"
    api.create_webhook(
        url="https://example.invalid/webhooks/events",
        watched=[{"type": "model", "name": corrected["MODEL_ID"]}],
        domains=["repo"],
        secret=corrected["WEBHOOK_SECRET"],
        token=False,
    )

    registered_routes: list[str] = []
    if diagnostics["gradio"]["ok"]:
        with warnings.catch_warnings(), redirect_stdout(captured_local_messages):
            warnings.simplefilter("ignore")
            local_server = WebhooksServer(webhook_secret=corrected["WEBHOOK_SECRET"])

            @local_server.add_webhook("events")
            async def events() -> dict[str, bool]:
                return {"accepted": True}

        registered_routes = sorted(local_server.registered_webhooks)
        assert registered_routes == ["/webhooks/events"]

    assert diagnostics["oauth"]["install"].startswith("Install")
    assert diagnostics["gradio"]["install"].startswith("Install")
    assert api.mock_calls  # intended lifecycle was captured by mocks, not HTTP

    return {
        "status": "ok",
        "network_calls": 0,
        "remote_mutations": 0,
        "mocked_client_calls": len(api.mock_calls),
        "invalid_config_error": invalid_error,
        "model_files": sorted(path.name for path in model_dir.iterdir()),
        "shards": sorted(set(index["weight_map"].values())),
        "dduf_entries": sorted(entries),
        "registered_routes": registered_routes,
        "captured_local_messages": [
            line for line in captured_local_messages.getvalue().splitlines() if line
        ],
        "optional_dependencies": diagnostics,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--work-dir",
        type=Path,
        help="Keep local fixture files in this directory; default uses a temporary directory.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON evidence.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with block_network():
        if args.work_dir is not None:
            report = run_fixture(args.work_dir)
            report["work_dir"] = str(args.work_dir)
        else:
            with tempfile.TemporaryDirectory(prefix="hf-hub-local-integration-") as tmp:
                report = run_fixture(Path(tmp))
                report["work_dir"] = "temporary (removed)"
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("local integration smoke: ok")
        print(f"  model files: {', '.join(report['model_files'])}")
        print(f"  shards: {', '.join(report['shards'])}")
        print(f"  DDUF entries: {', '.join(report['dduf_entries'])}")
        print(f"  mocked lifecycle calls: {report['mocked_client_calls']}")
        print("  network calls: 0; remote mutations: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
