#!/usr/bin/env python3
"""Inventory and, optionally, safely shape-check TD3 policy artifacts.

The default path only performs filesystem metadata checks. It intentionally does not
import torch or deserialize a .pth file. --load-state-dict is an explicit opt-in and
uses CPU + PyTorch's weights_only loader with a byte limit.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple

ACTOR_SHAPES: Dict[str, Tuple[int, ...]] = {
    "layer_1.weight": (800, 24),
    "layer_1.bias": (800,),
    "layer_2.weight": (600, 800),
    "layer_2.bias": (600,),
    "layer_3.weight": (2, 600),
    "layer_3.bias": (2,),
}

CRITIC_SHAPES: Dict[str, Tuple[int, ...]] = {
    "layer_1.weight": (800, 24),
    "layer_1.bias": (800,),
    "layer_2_s.weight": (600, 800),
    "layer_2_s.bias": (600,),
    "layer_2_a.weight": (600, 2),
    "layer_2_a.bias": (600,),
    "layer_3.weight": (1, 600),
    "layer_3.bias": (1,),
    "layer_4.weight": (800, 24),
    "layer_4.bias": (800,),
    "layer_5_s.weight": (600, 800),
    "layer_5_s.bias": (600,),
    "layer_5_a.weight": (600, 2),
    "layer_5_a.bias": (600,),
    "layer_6.weight": (1, 600),
    "layer_6.bias": (1,),
}

DEFAULT_MAX_BYTES = 256 * 1024 * 1024


def _shape_text(shape: Iterable[int]) -> str:
    return "[" + ", ".join(str(item) for item in shape) + "]"


def _safe_name(name: str) -> bool:
    """Reject path-like bases so the helper cannot escape model_dir."""
    return bool(name) and name not in {".", ".."} and Path(name).name == name


def _file_record(path: Path, max_bytes: int) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "regular_file": False,
        "symlink": path.is_symlink(),
        "size_bytes": None,
        "within_limit": False,
        "status": "missing",
    }
    if not path.exists():
        return record
    if path.is_symlink():
        record["status"] = "rejected_symlink"
        return record
    if not path.is_file():
        record["status"] = "rejected_not_regular_file"
        return record
    try:
        size = path.stat().st_size
    except OSError as exc:
        record["status"] = "stat_error: " + str(exc)
        return record
    record["regular_file"] = True
    record["size_bytes"] = size
    record["within_limit"] = size <= max_bytes
    record["status"] = "present" if record["within_limit"] else "rejected_too_large"
    return record


def _load_and_check(path: Path, expected: Mapping[str, Tuple[int, ...]], max_bytes: int) -> Dict[str, Any]:
    """Load a state dict only with an explicitly bounded weights-only torch loader."""
    result: Dict[str, Any] = {"load_attempted": True, "compatible": False}
    try:
        size = path.stat().st_size
    except OSError as exc:
        result["error"] = "could not stat before load: " + str(exc)
        return result
    if size > max_bytes:
        result["error"] = "file exceeds max byte limit before load"
        return result

    try:
        import torch  # Optional: default inventory mode never imports torch.
    except Exception as exc:  # pragma: no cover - depends on caller environment
        result["error"] = "PyTorch is unavailable: " + str(exc)
        return result

    try:
        parameters = inspect.signature(torch.load).parameters
    except (TypeError, ValueError) as exc:
        result["error"] = "cannot verify torch.load supports weights_only: " + str(exc)
        return result
    if "weights_only" not in parameters:
        result["error"] = "installed torch.load has no weights_only safety gate"
        return result

    try:
        loaded = torch.load(str(path), map_location="cpu", weights_only=True)
    except Exception as exc:
        result["error"] = "safe weights-only load failed: " + str(exc)
        return result
    if not isinstance(loaded, Mapping):
        result["error"] = "loaded object is not a state-dict mapping"
        return result

    keys = set(loaded.keys())
    expected_keys = set(expected.keys())
    missing = sorted(str(key) for key in expected_keys - keys)
    unexpected = sorted(str(key) for key in keys - expected_keys)
    wrong_shapes = []
    non_tensors = []
    for key in sorted(expected_keys & keys):
        value = loaded[key]
        if not isinstance(value, torch.Tensor):
            non_tensors.append(str(key))
            continue
        actual = tuple(int(dim) for dim in value.shape)
        wanted = expected[key]
        if actual != wanted:
            wrong_shapes.append(
                {"key": str(key), "expected": list(wanted), "actual": list(actual)}
            )

    result["keys"] = len(keys)
    result["missing_keys"] = missing
    result["unexpected_keys"] = unexpected
    result["non_tensor_keys"] = non_tensors
    result["wrong_shapes"] = wrong_shapes
    result["compatible"] = not (missing or unexpected or non_tensors or wrong_shapes)
    if not result["compatible"]:
        result["error"] = "state dict does not match the expected architecture"
    return result


def inspect_artifacts(
    model_dir: Path,
    name: str,
    load_state_dict: bool,
    max_bytes: int,
    require_critic: bool = False,
) -> Dict[str, Any]:
    actor = model_dir / (name + "_actor.pth")
    critic = model_dir / (name + "_critic.pth")
    result: Dict[str, Any] = {
        "model_dir": str(model_dir),
        "name": name,
        "expected": {
            "actor": str(actor),
            "critic": str(critic),
            "actor_shapes": {key: list(value) for key, value in ACTOR_SHAPES.items()},
            "critic_shapes": {key: list(value) for key, value in CRITIC_SHAPES.items()},
        },
        "load_state_dict": load_state_dict,
        "require_critic": require_critic,
        "max_bytes": max_bytes,
        "actor": _file_record(actor, max_bytes),
        "critic": _file_record(critic, max_bytes),
        "actor_only_ready": False,
        "complete_pair_ready": False,
    }

    if load_state_dict:
        for role, path, shapes in (
            ("actor", actor, ACTOR_SHAPES),
            ("critic", critic, CRITIC_SHAPES),
        ):
            record = result[role]
            if record["status"] == "present":
                record["validation"] = _load_and_check(path, shapes, max_bytes)
            else:
                record["validation"] = {"load_attempted": False}

    actor_record = result["actor"]
    actor_present = actor_record["status"] == "present"
    actor_compatible = (
        actor_record.get("validation", {}).get("compatible", False)
        if load_state_dict
        else False
    )
    critic_record = result["critic"]
    critic_present = critic_record["status"] == "present"
    critic_compatible = (
        critic_record.get("validation", {}).get("compatible", False)
        if load_state_dict and critic_present
        else False
    )
    result["actor_present"] = actor_present
    result["critic_present"] = critic_present
    result["actor_compatibility_verified"] = bool(load_state_dict and actor_compatible)
    result["critic_compatibility_verified"] = bool(load_state_dict and critic_present and critic_compatible)
    result["actor_only_ready"] = actor_compatible
    result["complete_pair_ready"] = actor_compatible and critic_compatible
    if not actor_present:
        result["overall_status"] = "missing_actor"
    elif not load_state_dict:
        result["overall_status"] = "actor_present_unverified"
    elif not actor_compatible:
        result["overall_status"] = "incompatible_actor"
    elif critic_present and not critic_compatible:
        result["overall_status"] = "actor_ready_critic_incompatible"
    elif not critic_present:
        result["overall_status"] = "actor_ready_critic_missing"
    else:
        result["overall_status"] = "pair_ready"
    return result


def _human_report(result: Mapping[str, Any]) -> str:
    actor = result["actor"]
    critic = result["critic"]
    lines = [
        "Policy artifact check",
        f"  model_dir: {result['model_dir']}",
        f"  base name: {result['name']}",
        f"  actor: {actor['status']} ({actor['path']})",
        f"  critic: {critic['status']} ({critic['path']})",
        f"  mode: {'safe weights-only shape check' if result['load_state_dict'] else 'metadata inventory (no tensor load)'}",
        f"  required gate: {'complete actor/critic pair' if result.get('require_critic') else 'actor-only'}",
    ]
    if result["load_state_dict"]:
        for role in ("actor", "critic"):
            validation = result[role].get("validation", {})
            if validation.get("load_attempted"):
                state = "compatible" if validation.get("compatible") else "INCOMPATIBLE"
                lines.append(f"  {role} state dict: {state}")
                if validation.get("error"):
                    lines.append(f"    reason: {validation['error']}")
                if validation.get("missing_keys"):
                    lines.append("    missing: " + ", ".join(validation["missing_keys"]))
                if validation.get("unexpected_keys"):
                    lines.append("    unexpected: " + ", ".join(validation["unexpected_keys"]))
                if validation.get("non_tensor_keys"):
                    lines.append("    non-tensors: " + ", ".join(validation["non_tensor_keys"]))
                for item in validation.get("wrong_shapes", []):
                    lines.append(
                        f"    wrong shape {item['key']}: expected {_shape_text(item['expected'])}, got {_shape_text(item['actual'])}"
                    )
    if not result["load_state_dict"] and result.get("actor_present"):
        actor_gate = "UNVERIFIED (rerun with --load-state-dict)"
        pair_gate = "UNVERIFIED (rerun with --load-state-dict)"
    else:
        actor_gate = "READY" if result["actor_only_ready"] else "NOT READY"
        pair_gate = "READY" if result["complete_pair_ready"] else "NOT READY"
    lines.extend(
        [
            f"  actor-only evaluation: {actor_gate}",
            f"  complete actor/critic pair: {pair_gate}",
            f"  overall status: {result['overall_status']}",
        ]
    )
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely inventory TD3 actor/critic artifacts; tensor loading is opt-in."
    )
    parser.add_argument("--model-dir", type=Path, help="Directory containing <name>_actor.pth and critic.")
    parser.add_argument("--name", help="Checkpoint base name, for example TD3_velodyne.")
    parser.add_argument(
        "--load-state-dict",
        action="store_true",
        help="Opt in to CPU, weights_only=True state-dict and exact-shape checks.",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_BYTES,
        help=f"Maximum size of each artifact in bytes (default: {DEFAULT_MAX_BYTES}).",
    )
    parser.add_argument(
        "--require-critic",
        action="store_true",
        help="Require a compatible actor/critic pair for success instead of actor-only readiness.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a JSON report instead of human-readable text.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run a temporary-file inventory fixture without importing torch.",
    )
    return parser


def run_self_test() -> int:
    """Exercise parser-adjacent inventory behavior without touching the runtime tree."""
    with tempfile.TemporaryDirectory(prefix="policy-artifact-self-test-") as directory:
        model_dir = Path(directory)
        actor = model_dir / "fixture_actor.pth"
        critic = model_dir / "fixture_critic.pth"
        actor.write_bytes(b"not deserialized in inventory mode")
        first = inspect_artifacts(model_dir, "fixture", load_state_dict=False, max_bytes=1024)
        assert first["actor_present"] and not first["actor_only_ready"]
        assert first["overall_status"] == "actor_present_unverified"
        critic.write_bytes(b"fixture")
        second = inspect_artifacts(model_dir, "fixture", load_state_dict=False, max_bytes=1024)
        assert second["critic_present"] and not second["complete_pair_ready"]
    print("self-test: PASS (metadata inventory only; no tensor was loaded)")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    if args.model_dir is None or args.name is None:
        parser.error("--model-dir and --name are required unless --self-test is used")
    if not _safe_name(args.name):
        parser.error("--name must be a plain checkpoint base name without path separators")
    if args.max_bytes <= 0:
        parser.error("--max-bytes must be positive")
    model_dir = args.model_dir
    if not model_dir.exists():
        result = {
            "model_dir": str(model_dir),
            "name": args.name,
            "overall_status": "missing_model_dir",
            "actor_only_ready": False,
            "complete_pair_ready": False,
            "actor_present": False,
            "critic_present": False,
            "require_critic": args.require_critic,
        }
    elif not model_dir.is_dir():
        result = {
            "model_dir": str(model_dir),
            "name": args.name,
            "overall_status": "model_dir_not_directory",
            "actor_only_ready": False,
            "complete_pair_ready": False,
            "actor_present": False,
            "critic_present": False,
            "require_critic": args.require_critic,
        }
    else:
        result = inspect_artifacts(
            model_dir,
            args.name,
            args.load_state_dict,
            args.max_bytes,
            args.require_critic,
        )

    ready = result.get("complete_pair_ready") if args.require_critic else result.get("actor_only_ready")
    result["requested_gate_ready"] = bool(ready)
    print(json.dumps(result, indent=2, sort_keys=True) if args.json else _human_report(result))
    return 0 if ready else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        # Keep shell pipelines quiet when a consumer closes early.
        try:
            sys.stderr.close()
        finally:
            raise SystemExit(0)
