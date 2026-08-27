#!/usr/bin/env python3
"""Read-only structural and timing checks for resolved AlpaSim runtime YAML.

This helper intentionally does not import AlpaSim, contact gRPC services, start
containers, download assets, or modify files. It is useful before a live run;
full service/version/scene validation still happens during runtime startup.

Example:
  python inspect_runtime_config.py --user-config user.yaml \\
      --network-config network.yaml
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - depends on caller environment
    raise SystemExit("Missing optional dependency 'PyYAML'; install it to parse YAML.") from exc

SERVICES = ("driver", "renderer", "physics", "trafficsim", "controller")


def _load(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
    except OSError as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return value


def _integer(mapping: dict[str, Any], key: str, default: int | None = None) -> int | None:
    value = mapping.get(key, default)
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer, not boolean")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer, got {value!r}") from exc


def _check_user_config(config: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    sim = config.get("simulation_config")
    if not isinstance(sim, dict):
        return ["simulation_config must be a mapping"], warnings
    endpoints = config.get("endpoints", {})
    if not isinstance(endpoints, dict):
        errors.append("endpoints must be a mapping")
        endpoints = {}

    control = _integer(sim, "control_timestep_us")
    if control is None or control <= 0:
        errors.append("simulation_config.control_timestep_us must be positive")
    force_gt = _integer(sim, "force_gt_duration_us", 0)
    if force_gt is None or force_gt < 0:
        errors.append("simulation_config.force_gt_duration_us must be >= 0")

    cameras = sim.get("cameras", [])
    if not isinstance(cameras, list) or not cameras:
        errors.append("simulation_config.cameras must be a non-empty list")
        cameras = []
    intervals: list[int] = []
    for index, camera in enumerate(cameras):
        if not isinstance(camera, dict):
            errors.append(f"simulation_config.cameras[{index}] must be a mapping")
            continue
        interval = _integer(camera, "frame_interval_us")
        if interval is None or interval <= 0:
            errors.append(f"camera {index} frame_interval_us must be positive")
        else:
            intervals.append(interval)
        shutter = _integer(camera, "shutter_duration_us", 0)
        if shutter is not None and shutter < 0:
            errors.append(f"camera {index} shutter_duration_us must be >= 0")

    zero_delay = bool(sim.get("assert_zero_decision_delay", False))
    if zero_delay and control and intervals:
        for interval in intervals:
            if control % interval:
                errors.append(
                    "zero-delay cadence mismatch: control_timestep_us "
                    f"{control} is not a multiple of camera frame_interval_us {interval}"
                )

    physics_mode = str(sim.get("physics_update_mode", "NONE"))
    physics_skip = bool(endpoints.get("physics", {}).get("skip", False)) if isinstance(endpoints.get("physics"), dict) else False
    if physics_skip and physics_mode != "NONE":
        errors.append("physics service is skipped but physics_update_mode is not NONE")
    if not physics_skip and physics_mode == "NONE":
        warnings.append("physics service is enabled while physics_update_mode is NONE")

    renderer = config.get("renderer", {})
    if not isinstance(renderer, dict):
        errors.append("renderer must be a mapping")
        renderer = {}
    kind = renderer.get("kind", "sensorsim")
    if kind == "video_model":
        vm = renderer.get("video_model_config") or {}
        if not isinstance(vm, dict):
            errors.append("renderer.video_model_config must be a mapping for video_model")
            vm = {}
        fps = _integer(vm, "fps", 30)
        first = _integer(vm, "first_chunk_frames", 5)
        regular = _integer(vm, "chunk_frames", 8)
        if not fps or fps <= 0:
            errors.append("video_model_config.fps must be positive")
        if not first or first <= 0:
            errors.append("video_model_config.first_chunk_frames must be positive")
        if not regular or regular <= 0:
            errors.append("video_model_config.chunk_frames must be positive")
        if vm.get("frame_forwarding_mode", "all") not in {"all", "subsample"}:
            errors.append("video_model_config.frame_forwarding_mode must be all or subsample")
        if vm.get("forward_hdmap_to_driver", False) and not vm.get("return_hdmap_frames", False):
            errors.append("forward_hdmap_to_driver requires return_hdmap_frames")
        if fps and first and regular and force_gt and control:
            frame_interval = 1_000_000 // fps
            first_duration = first * frame_interval
            regular_duration = regular * frame_interval
            if control != regular_duration:
                errors.append(
                    "video-model cadence mismatch: control_timestep_us "
                    f"{control} != chunk_frames * floor(1e6/fps) {regular_duration}"
                )
            minimum = first_duration + regular_duration
            if force_gt < minimum:
                errors.append(
                    "video-model force-GT duration is shorter than first plus one regular chunk "
                    f"({minimum} us)"
                )
            elif (force_gt - first_duration) % regular_duration:
                errors.append("video-model force-GT duration leaves a partial regular chunk")
    elif kind != "sensorsim":
        errors.append(f"renderer.kind must be sensorsim or video_model, got {kind!r}")

    nr_workers = _integer(config, "nr_workers")
    if nr_workers is not None and nr_workers < 1:
        errors.append("nr_workers must be >= 1")
    for service in SERVICES:
        value = endpoints.get(service, {})
        if isinstance(value, dict):
            concurrency = _integer(value, "n_concurrent_rollouts", 0)
            if concurrency is not None and concurrency < 0:
                errors.append(f"endpoints.{service}.n_concurrent_rollouts must be >= 0")
    return errors, warnings


def _check_network_config(
    config: dict[str, Any], user_config: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    user_endpoints = user_config.get("endpoints", {})
    for service in SERVICES:
        user_section = user_endpoints.get(service, {})
        skipped = isinstance(user_section, dict) and bool(user_section.get("skip", False))
        section = config.get(service)
        if skipped and section is None:
            continue
        if not isinstance(section, dict):
            errors.append(f"network config missing service mapping: {service}")
            continue
        endpoints = section.get("endpoints")
        if skipped and (endpoints is None or endpoints == []):
            continue
        if not isinstance(endpoints, list) or not endpoints:
            errors.append(f"network config has no endpoints for non-skipped service: {service}")
            continue
        for index, endpoint in enumerate(endpoints):
            if not isinstance(endpoint, dict) or not endpoint.get("address"):
                errors.append(f"network config endpoint {service}[{index}] has no address")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--user-config", required=True, type=Path)
    parser.add_argument("--network-config", type=Path)
    parser.add_argument("--json", action="store_true", help="emit machine-readable results")
    args = parser.parse_args(argv)

    try:
        user = _load(args.user_config)
        errors, warnings = _check_user_config(user)
        if args.network_config:
            errors.extend(_check_network_config(_load(args.network_config), user))
    except ValueError as exc:
        errors, warnings = [str(exc)], []

    result = {"ok": not errors, "errors": errors, "warnings": warnings}
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for warning in warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print("runtime config checks passed" if not errors else "runtime config checks failed")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
