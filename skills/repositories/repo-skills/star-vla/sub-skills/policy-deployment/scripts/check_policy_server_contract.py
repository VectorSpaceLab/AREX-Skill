#!/usr/bin/env python3
"""Validate StarVLA policy-server request and metadata contracts.

This helper is safe by default: it does not load checkpoints, import StarVLA,
or open network sockets. It validates JSON-shaped websocket requests, validates
metadata JSON captured from a server handshake, prints built-in examples, and
can optionally exercise the GR00T custom ZMQ ndarray msgpack codec locally when
numpy/msgpack are installed.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.notes.append(message)

    def extend(self, other: "Report") -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.notes.extend(other.notes)


def _load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def _shape_from_nested_list(value: Any, max_depth: int = 6) -> list[int] | None:
    """Infer a JSON nested-list shape from the first branch.

    This is intended for small samples. Large arrays should be represented as a
    descriptor such as {"shape": [224, 224, 3], "dtype": "uint8"}.
    """
    shape: list[int] = []
    cur = value
    depth = 0
    while isinstance(cur, list) and depth < max_depth:
        shape.append(len(cur))
        if not cur:
            break
        cur = cur[0]
        depth += 1
    return shape or None


def _shape_of(value: Any) -> list[int] | None:
    if isinstance(value, dict):
        shape = value.get("shape") or value.get("__shape__")
        if isinstance(shape, list) and all(isinstance(x, int) for x in shape):
            return list(shape)
        if isinstance(value.get("data"), list):
            return _shape_from_nested_list(value["data"])
    if isinstance(value, list):
        return _shape_from_nested_list(value)
    return None


def _dtype_of(value: Any) -> str | None:
    if isinstance(value, dict):
        dtype = value.get("dtype") or value.get("__dtype__")
        if dtype is not None:
            return str(dtype)
    return None


def _as_image_list(value: Any) -> list[Any] | None:
    if value is None:
        return None
    if isinstance(value, list):
        return value
    return [value]


def _payload_from_request(request: Any, report: Report) -> tuple[str, dict[str, Any] | None]:
    if not isinstance(request, dict):
        report.error(f"request must be a JSON object, got {type(request).__name__}")
        return "invalid", None

    msg_type = request.get("type", "infer")
    if msg_type == "ping":
        report.note("request is a websocket ping; no inference payload is required")
        return "ping", {}

    if msg_type not in {"infer", "predict_action"}:
        report.warn(
            f"websocket server code only routes ping/infer/predict_action; "
            f"type={msg_type!r} may be unsupported"
        )

    payload = request.get("payload", request)
    if not isinstance(payload, dict):
        report.error(f"payload must be an object, got {type(payload).__name__}")
        return str(msg_type), None
    return str(msg_type), payload


def _metadata_available_keys(metadata: dict[str, Any] | None) -> list[str]:
    if not isinstance(metadata, dict):
        return []
    keys = metadata.get("available_unnorm_keys")
    return [str(k) for k in keys] if isinstance(keys, list) else []


def _metadata_default_key(metadata: dict[str, Any] | None) -> str | None:
    if not isinstance(metadata, dict):
        return None
    value = metadata.get("default_unnorm_key")
    return None if value is None else str(value)


def _metadata_expected_hw(metadata: dict[str, Any] | None) -> tuple[int, int] | None:
    if not isinstance(metadata, dict):
        return None
    size = metadata.get("training_obs_image_size")
    if isinstance(size, list) and len(size) == 2 and all(isinstance(x, int) for x in size):
        return int(size[0]), int(size[1])
    return None


def validate_metadata(metadata: Any) -> Report:
    report = Report()
    if not isinstance(metadata, dict):
        report.error(f"metadata must be a JSON object, got {type(metadata).__name__}")
        return report

    chunk = metadata.get("action_chunk_size")
    if not isinstance(chunk, int) or chunk <= 0:
        report.error("metadata.action_chunk_size must be a positive integer")
    else:
        report.note(f"metadata action_chunk_size={chunk}")

    keys = metadata.get("available_unnorm_keys")
    if not isinstance(keys, list) or not all(isinstance(k, str) for k in keys):
        report.error("metadata.available_unnorm_keys must be a list of strings")
    elif len(keys) == 0:
        report.warn("metadata.available_unnorm_keys is empty; unnormalization key selection cannot be checked")
    else:
        report.note(f"metadata available_unnorm_keys={keys}")

    default_key = metadata.get("default_unnorm_key")
    if default_key is not None and not isinstance(default_key, str):
        report.error("metadata.default_unnorm_key must be null or a string")
    if isinstance(keys, list) and len(keys) > 1 and default_key is None:
        report.note("metadata is multi-key lazy mode; inference requests must include top-level unnorm_key")

    image_size = metadata.get("training_obs_image_size")
    if image_size is None:
        report.note("metadata.training_obs_image_size is null or absent; image size must be checked from training docs/config")
    elif not (isinstance(image_size, list) and len(image_size) == 2 and all(isinstance(x, int) for x in image_size)):
        report.error("metadata.training_obs_image_size must be null or [H, W] integers")
    else:
        report.note(f"metadata training_obs_image_size={image_size}")

    if "expected_image_size" in metadata:
        report.warn("metadata.expected_image_size is not the inspected StarVLA field; prefer training_obs_image_size")

    for field_name in ("action_keys", "state_keys"):
        if field_name in metadata:
            value = metadata[field_name]
            if not isinstance(value, list) or not all(isinstance(k, str) for k in value):
                report.error(f"metadata.{field_name} must be a list of strings when present")
            else:
                report.note(f"metadata {field_name} count={len(value)}")

    for field_name in ("action_key_dims", "state_key_dims"):
        if field_name in metadata:
            dims = metadata[field_name]
            if not isinstance(dims, dict) or not all(isinstance(k, str) and isinstance(v, int) and v > 0 for k, v in dims.items()):
                report.error(f"metadata.{field_name} must be a mapping of string keys to positive integer dims")
            else:
                report.note(f"metadata {field_name} total_dim={sum(dims.values())}")

    return report


def validate_request(request: Any, metadata: dict[str, Any] | None = None) -> Report:
    report = Report()
    msg_type, payload = _payload_from_request(request, report)
    if msg_type == "ping" or payload is None:
        return report

    examples = payload.get("examples")
    if not isinstance(examples, list) or len(examples) == 0:
        report.error("payload.examples must be a non-empty list")
        return report

    available = _metadata_available_keys(metadata)
    default_key = _metadata_default_key(metadata)
    unnorm_key = payload.get("unnorm_key")
    if available:
        if len(available) > 1 and default_key is None and not unnorm_key:
            report.error(
                "metadata has multiple available_unnorm_keys and no default; payload must include top-level unnorm_key"
            )
        if unnorm_key is not None and str(unnorm_key) not in available:
            report.error(f"payload.unnorm_key={unnorm_key!r} is not in metadata.available_unnorm_keys={available}")
        elif unnorm_key is not None:
            report.note(f"payload unnorm_key={unnorm_key!r} matches metadata")
    elif unnorm_key is None:
        report.warn("payload has no unnorm_key and no metadata was provided to prove a single-key checkpoint")

    if payload.get("expect_response_key") == "normalized_actions":
        report.warn("client expectation mentions normalized_actions; current StarVLA server returns data.actions")

    expected_hw = _metadata_expected_hw(metadata)

    for i, example in enumerate(examples):
        if not isinstance(example, dict):
            report.error(f"examples[{i}] must be an object")
            continue

        images = _as_image_list(example.get("image"))
        if images is None or len(images) == 0:
            report.error(f"examples[{i}].image is required and must contain at least one view")
        else:
            report.note(f"examples[{i}] image view count={len(images)}")
            for j, image in enumerate(images):
                shape = _shape_of(image)
                dtype = _dtype_of(image)
                label = f"examples[{i}].image[{j}]"
                if shape is None:
                    report.warn(f"{label} has no shape descriptor; expected [H, W, 3]")
                elif len(shape) != 3 or shape[-1] != 3:
                    report.error(f"{label} shape should be [H, W, 3], got {shape}")
                else:
                    if expected_hw is not None and (shape[0], shape[1]) != expected_hw:
                        report.warn(f"{label} shape {shape[:2]} differs from metadata.training_obs_image_size={list(expected_hw)}")
                    else:
                        report.note(f"{label} shape={shape}")
                if dtype is not None and dtype.lower() not in {"uint8", "uint8_t"}:
                    report.warn(f"{label} dtype is {dtype!r}; ordinary image requests should use uint8 RGB")

        lang = example.get("lang")
        if lang is None:
            report.warn(f"examples[{i}].lang is absent; only use this if the checkpoint/client supplies a fallback instruction")
        elif not isinstance(lang, str):
            report.error(f"examples[{i}].lang must be a string when present")

        if "state" in example:
            state_shape = _shape_of(example["state"])
            if state_shape is None:
                report.warn(f"examples[{i}].state has no shape descriptor; expected flat [D] or batched [1, D]")
            elif len(state_shape) == 1:
                report.note(f"examples[{i}].state shape={state_shape}; flat state is client-specific, verify training order")
            elif len(state_shape) == 2 and state_shape[0] == 1:
                report.note(f"examples[{i}].state shape={state_shape}")
            else:
                report.warn(f"examples[{i}].state shape {state_shape} is unusual; expected [D] or [1, D]")

    return report


def _example_metadata() -> dict[str, Any]:
    return {
        "env": "starvla_policy_server",
        "action_chunk_size": 8,
        "available_unnorm_keys": ["new_embodiment"],
        "default_unnorm_key": "new_embodiment",
        "training_data_mix": "example_mix",
        "training_obs_image_size": [224, 224],
        "eval_image_contract": "Eval clients must explicitly choose image count and order.",
        "action_keys": ["action.joints", "action.gripper"],
        "state_keys": ["state.joints", "state.gripper"],
    }


def _example_request() -> dict[str, Any]:
    return {
        "type": "infer",
        "request_id": "request-001",
        "payload": {
            "examples": [
                {
                    "image": [
                        {"shape": [224, 224, 3], "dtype": "uint8", "description": "RGB camera view placeholder"}
                    ],
                    "lang": "pick up the red cup",
                    "state": {"shape": [1, 8], "dtype": "float32", "description": "optional proprioception placeholder"},
                }
            ],
            "unnorm_key": "new_embodiment",
        },
    }


def _example_gr00t_modality_config() -> dict[str, Any]:
    return {
        "state_keys": ["state.left_arm", "state.right_arm"],
        "state_key_dims": {"state.left_arm": 7, "state.right_arm": 7},
        "action_keys": ["action.left_arm", "action.right_arm", "action.gripper"],
        "action_key_dims": {"action.left_arm": 7, "action.right_arm": 7, "action.gripper": 1},
        "unnorm_key": "unitree_g1_wbc",
    }


def print_examples() -> None:
    print("# Example websocket metadata")
    print(json.dumps(_example_metadata(), indent=2))
    print("\n# Example websocket inference request")
    print(json.dumps(_example_request(), indent=2))
    print("\n# Example GR00T modality config")
    print(json.dumps(_example_gr00t_modality_config(), indent=2))


def check_zmq_codec() -> Report:
    report = Report()
    try:
        import msgpack  # type: ignore
        import numpy as np  # type: ignore
    except Exception as exc:  # noqa: BLE001
        report.warn(f"skipping ZMQ custom codec check because optional dependency import failed: {exc}")
        return report

    def encode(obj: Any) -> Any:
        if isinstance(obj, np.ndarray):
            buf = io.BytesIO()
            np.save(buf, obj, allow_pickle=False)
            return {"__ndarray_class__": True, "as_npy": buf.getvalue()}
        if isinstance(obj, (np.floating, np.integer)):
            return obj.item()
        return obj

    def decode(obj: Any) -> Any:
        if isinstance(obj, dict) and "__ndarray_class__" in obj:
            return np.load(io.BytesIO(obj["as_npy"]), allow_pickle=False)
        return obj

    payload = {
        "endpoint": "get_action",
        "data": {
            "observation": {
                "video": {"ego_view": np.zeros((1, 1, 2, 3, 3), dtype=np.uint8)},
                "state": {"left_arm": np.ones((1, 1, 7), dtype=np.float32)},
                "language": {"annotation.human.task_description": [["demo"]]},
            },
            "options": None,
        },
    }
    packed = msgpack.packb(payload, default=encode, strict_types=False)
    unpacked = msgpack.unpackb(packed, object_hook=decode, raw=False)
    image = unpacked["data"]["observation"]["video"]["ego_view"]
    state = unpacked["data"]["observation"]["state"]["left_arm"]
    if image.shape != (1, 1, 2, 3, 3) or image.dtype != np.uint8:
        report.error("ZMQ codec image roundtrip failed")
    if state.shape != (1, 1, 7) or state.dtype != np.float32:
        report.error("ZMQ codec state roundtrip failed")
    if not report.errors:
        report.note("ZMQ custom ndarray codec roundtrip OK; no sockets were opened")
    return report


def print_report(report: Report) -> None:
    for message in report.notes:
        print(f"NOTE: {message}")
    for message in report.warnings:
        print(f"WARNING: {message}")
    for message in report.errors:
        print(f"ERROR: {message}")
    if not report.errors:
        print("OK: no contract errors found")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-json", help="Path to a websocket-style request JSON file to validate.")
    parser.add_argument("--metadata-json", help="Path to server metadata JSON captured from a handshake or logs.")
    parser.add_argument("--print-examples", action="store_true", help="Print built-in metadata/request examples and exit unless other checks are requested.")
    parser.add_argument("--check-zmq-codec", action="store_true", help="Exercise the GR00T custom msgpack ndarray codec locally if numpy/msgpack are installed.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not any([args.request_json, args.metadata_json, args.print_examples, args.check_zmq_codec]):
        print_examples()
        return 0

    if args.print_examples:
        print_examples()

    report = Report()
    metadata: dict[str, Any] | None = None
    if args.metadata_json:
        loaded = _load_json(args.metadata_json)
        meta_report = validate_metadata(loaded)
        report.extend(meta_report)
        if isinstance(loaded, dict):
            metadata = loaded

    if args.request_json:
        request = _load_json(args.request_json)
        report.extend(validate_request(request, metadata=metadata))

    if args.check_zmq_codec:
        report.extend(check_zmq_codec())

    if args.request_json or args.metadata_json or args.check_zmq_codec:
        print_report(report)

    if report.errors or (args.strict and report.warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
