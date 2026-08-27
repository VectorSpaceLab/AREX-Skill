#!/usr/bin/env python3
"""Inspect LeRobot environment dispatch without starting a simulator.

This probe is deliberately non-invasive. It constructs an EnvConfig dataclass,
reads static metadata, and checks whether likely optional distributions are
findable. It does not import benchmark packages, call make_env(), download
assets/weights, access the Hub, reset/step environments, or create a render
context.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import sys
from dataclasses import fields
from typing import Any


PACKAGE_CANDIDATES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "pusht": (("gym_pusht",), ("gym-pusht",)),
    "aloha": (("gym_aloha",), ("gym-aloha",)),
    "libero": (("libero",), ("hf-libero",)),
    "libero_plus": (("libero",), ("LIBERO-plus",)),
    "metaworld": (("metaworld",), ("metaworld",)),
    "robotwin": (("envs", "sapien", "curobo"), ("sapien", "curobo")),
    "vlabench": (("VLABench", "dm_control", "mujoco"), ("VLABench", "dm-control", "mujoco")),
    "robocasa": (("robocasa", "robosuite", "mujoco"), ("robocasa", "robosuite", "mujoco")),
    "robomme": (("robomme", "sapien"), ("robomme", "mani-skill", "sapien")),
    "gym_manipulator": (("gym_hil",), ("gym-hil",)),
}


def _find_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def _distribution_versions(names: tuple[str, ...]) -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
        except Exception as exc:  # pragma: no cover - metadata implementations vary
            versions[name] = f"error:{type(exc).__name__}"
    return versions


def _feature_summary(cfg: Any) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for key, feature in getattr(cfg, "features", {}).items():
        shape = getattr(feature, "shape", None)
        feature_type = getattr(feature, "type", None)
        result[str(key)] = {
            "shape": list(shape) if shape is not None else None,
            "type": getattr(feature_type, "value", str(feature_type)),
            "mapped_to": getattr(cfg, "features_map", {}).get(key),
        }
    return result


def _field_names(cfg: Any) -> list[str]:
    try:
        return [field.name for field in fields(cfg)]
    except TypeError:
        return []


def _package_status(env_type: str) -> dict[str, Any]:
    module_names, distribution_names = PACKAGE_CANDIDATES.get(env_type, ((), ()))
    modules = {name: _find_module(name) for name in module_names}
    distributions = _distribution_versions(distribution_names)
    core = _distribution_versions(("lerobot", "gymnasium", "numpy"))
    notes: list[str] = []
    if env_type == "metaworld" and distributions.get("metaworld") not in (None, "3.0.0"):
        notes.append("LeRobot documents MetaWorld 3.0.0; inspect the installed Gymnasium pairing before rollout.")
    if env_type == "robomme":
        notes.append("RoboMME commonly needs an isolated NumPy 1.x/Gymnasium 0.29.x environment; this is not a resolver fix.")
    if env_type == "libero_plus":
        notes.append("The plus fork and vanilla LIBERO share an import namespace; verify which implementation is active.")
    if not module_names:
        status = "not-applicable-or-hub"
    elif all(modules.values()):
        status = "present"
    elif any(modules.values()):
        status = "partial"
    else:
        status = "missing"
    return {
        "status": status,
        "modules": modules,
        "distribution_versions": distributions,
        "core_distribution_versions": core,
        "notes": notes,
    }


def build_report(env_type: str, task: str | None, kwargs: dict[str, Any]) -> dict[str, Any]:
    report: dict[str, Any] = {
        "probe": "environment-dispatch-only",
        "safety": {
            "imports_benchmark_packages": False,
            "calls_make_env": False,
            "creates_or_resets_simulator": False,
            "downloads_assets_or_weights": False,
            "uses_credentials_or_remote_code": False,
        },
        "requested": {"env_type": env_type, "task": task, "kwargs": kwargs},
    }
    try:
        from lerobot.envs.configs import EnvConfig
        from lerobot.envs.factory import make_env_config

        known = sorted(str(name) for name in EnvConfig.get_known_choices())
        report["known_env_types"] = known
        config_kwargs = dict(kwargs)
        if task is not None:
            config_kwargs.setdefault("task", task)
        cfg = make_env_config(env_type, **config_kwargs)
        report["config_status"] = "ok"
        report["config"] = {
            "type": cfg.type,
            "class": type(cfg).__name__,
            "fields": _field_names(cfg),
            "gym_id": getattr(cfg, "gym_id", None),
            "package_name": getattr(cfg, "package_name", None),
            "gym_kwargs_repr": repr(getattr(cfg, "gym_kwargs", {})),
            "features": _feature_summary(cfg),
            "features_map": dict(getattr(cfg, "features_map", {})),
        }
        report["package_status"] = _package_status(env_type)
    except Exception as exc:
        report["config_status"] = "error"
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
        report["known_env_types"] = []
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect LeRobot EnvConfig dispatch without importing or running an external simulator."
    )
    parser.add_argument("--env-type", help="Registered EnvConfig name, for example pusht or libero.")
    parser.add_argument("--task", help="Optional task/suite override passed to the dataclass.")
    parser.add_argument(
        "--kwargs",
        default="{}",
        help="JSON object of additional safe dataclass fields; no runtime factory fields are accepted.",
    )
    parser.add_argument(
        "--show-known",
        action="store_true",
        help="Print registered environment names without constructing a config.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        from lerobot.envs.configs import EnvConfig

        known = sorted(str(name) for name in EnvConfig.get_known_choices())
    except Exception as exc:
        print(json.dumps({"probe": "environment-dispatch-only", "config_status": "import-error", "error": str(exc)}))
        return 1

    if args.show_known and args.env_type is None:
        print(json.dumps({"probe": "environment-dispatch-only", "known_env_types": known}, indent=2))
        return 0
    if not args.env_type:
        print("--env-type is required unless --show-known is used", file=sys.stderr)
        return 2
    try:
        kwargs = json.loads(args.kwargs)
        if not isinstance(kwargs, dict):
            raise ValueError("--kwargs must decode to a JSON object")
    except (json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"config_status": "invalid-input", "error": str(exc)}))
        return 2

    report = build_report(args.env_type, args.task, kwargs)
    report["known_env_types"] = known
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    return 0 if report.get("config_status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
