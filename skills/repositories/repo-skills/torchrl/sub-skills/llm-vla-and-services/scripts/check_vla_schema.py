#!/usr/bin/env python3
"""CPU-safe TorchRL VLA schema/action smoke test.

This helper creates tiny TensorDict fixtures and checks the canonical VLA
validator, uniform action tokenization, action chunking, and explicit-stat
action scaling. It performs no downloads, rendering, training, or GPU work.

Examples:
    python check_vla_schema.py
    python check_vla_schema.py --repo-root /path/to/pytorch-rl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _prepend_repo_root(repo_root: str | None) -> None:
    if repo_root:
        root = Path(repo_root).expanduser().resolve()
        sys.path.insert(0, str(root))


def _import_deps() -> dict[str, Any]:
    try:
        import torch
        from tensordict import NonTensorData, TensorDict
        from torchrl.data.vla import UniformActionTokenizer, validate_vla_tensordict
        from torchrl.envs.transforms import ActionChunkTransform, ActionScaling
    except Exception as exc:  # pragma: no cover - user-facing diagnostic path
        print(
            json.dumps(
                {
                    "status": "import_error",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                    "hint": (
                        "Install TorchRL with its base dependencies, or pass "
                        "--repo-root for an editable checkout that is importable."
                    ),
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    return {
        "torch": torch,
        "NonTensorData": NonTensorData,
        "TensorDict": TensorDict,
        "UniformActionTokenizer": UniformActionTokenizer,
        "validate_vla_tensordict": validate_vla_tensordict,
        "ActionChunkTransform": ActionChunkTransform,
        "ActionScaling": ActionScaling,
    }


def _valid_vla_td(torch, TensorDict, NonTensorData):
    return TensorDict(
        {
            "observation": {
                "image": torch.zeros(2, 3, 8, 8, dtype=torch.uint8),
                "state": torch.zeros(2, 4),
            },
            "language_instruction": NonTensorData("pick up the red block"),
            "action": torch.zeros(2, 3),
        },
        batch_size=[2],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        help=(
            "Optional TorchRL checkout root to prepend to sys.path before imports. "
            "Use only when the package is not already installed."
        ),
    )
    args = parser.parse_args(argv)
    _prepend_repo_root(args.repo_root)
    deps = _import_deps()

    torch = deps["torch"]
    TensorDict = deps["TensorDict"]
    NonTensorData = deps["NonTensorData"]
    validate_vla_tensordict = deps["validate_vla_tensordict"]
    UniformActionTokenizer = deps["UniformActionTokenizer"]
    ActionChunkTransform = deps["ActionChunkTransform"]
    ActionScaling = deps["ActionScaling"]

    report: dict[str, Any] = {"status": "ok"}

    valid = _valid_vla_td(torch, TensorDict, NonTensorData)
    valid_issues = validate_vla_tensordict(valid, raise_on_error=False)
    if valid_issues:
        raise AssertionError(f"valid VLA fixture unexpectedly failed: {valid_issues}")
    report["valid_schema"] = "passed"

    invalid = TensorDict(
        {
            "observation": {},
            "action": torch.tensor([[0.0, float("nan"), 0.0], [0.0, 0.0, 0.0]]),
        },
        batch_size=[2],
    )
    invalid_issues = validate_vla_tensordict(invalid, raise_on_error=False)
    expected_fragments = [
        "language instruction",
        "no perception",
        "non-finite",
    ]
    missing = [
        frag for frag in expected_fragments if not any(frag in issue for issue in invalid_issues)
    ]
    if missing:
        raise AssertionError(
            f"invalid VLA fixture missed expected diagnostics {missing}: {invalid_issues}"
        )
    try:
        validate_vla_tensordict(invalid)
    except ValueError as exc:
        report["invalid_schema_error"] = str(exc).splitlines()[0]
    else:
        raise AssertionError("validate_vla_tensordict(..., raise_on_error=True) did not raise")
    report["invalid_schema_issues"] = invalid_issues

    tokenizer = UniformActionTokenizer(256, low=-1.0, high=1.0)
    encoded = tokenizer.encode(torch.tensor([-1.0, 0.0, 1.0]))
    if encoded.tolist() != [0, 128, 255]:
        raise AssertionError(f"unexpected tokenizer output: {encoded.tolist()}")
    decoded = tokenizer.decode(encoded)
    report["uniform_tokenizer"] = {
        "encoded": encoded.tolist(),
        "decoded_rounded": [round(float(x), 4) for x in decoded.tolist()],
        "vocab_size": tokenizer.vocab_size,
    }

    chunker = ActionChunkTransform(chunk_size=3)
    chunk_input = TensorDict(
        {
            "action": torch.arange(4).view(1, 4, 1).float(),
            ("next", "done"): torch.tensor([False, True, False, False]).view(1, 4, 1),
        },
        batch_size=[1, 4],
    )
    chunked = chunker(chunk_input.clone())
    expected = torch.tensor([[0.0, 1.0, 1.0], [1.0, 1.0, 1.0], [2.0, 3.0, 3.0], [3.0, 3.0, 3.0]])
    actual = chunked["vla_action", "chunk"][0, :, :, 0]
    torch.testing.assert_close(actual, expected)
    report["action_chunk"] = {
        "chunk_shape": list(chunked["vla_action", "chunk"].shape),
        "pad_mask": chunked["action_is_pad"][0].tolist(),
    }

    scaler = ActionScaling.from_stats(
        mean=torch.tensor([1.0, 2.0]),
        std=torch.tensor([2.0, 4.0]),
        in_keys_inv=[],
    )
    scaled_td = scaler(
        TensorDict({"action": torch.tensor([[3.0, 6.0]])}, batch_size=[1])
    )
    torch.testing.assert_close(scaled_td["action"], torch.tensor([[1.0, 1.0]]))
    denorm = scaler.denormalize(torch.tensor([[1.0, 1.0]]))
    torch.testing.assert_close(denorm, torch.tensor([[3.0, 6.0]]))
    report["action_scaling"] = {
        "normalized": scaled_td["action"].tolist(),
        "denormalized": denorm.tolist(),
    }

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
