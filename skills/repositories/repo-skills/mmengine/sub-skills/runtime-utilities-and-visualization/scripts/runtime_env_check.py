#!/usr/bin/env python3
"""Safe MMEngine runtime utilities diagnostic.

This script performs local-only checks: imports MMEngine runtime utilities,
prints a compact environment summary, writes tiny visualizer artifacts under a
temporary or user-provided directory, and reports distributed state without
initializing a process group.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict


def _json_default(value: Any) -> str:
    return str(value)


def _status(name: str, ok: bool, detail: str = "") -> None:
    prefix = "OK" if ok else "WARN"
    suffix = f": {detail}" if detail else ""
    print(f"[{prefix}] {name}{suffix}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run safe local MMEngine runtime checks for logging, "
            "visualization, device, environment, and distributed helpers."
        )
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help=(
            "Directory for temporary LocalVisBackend outputs. If omitted, a "
            "temporary directory is created and kept only for this process."
        ),
    )
    parser.add_argument(
        "--skip-visualizer",
        action="store_true",
        help="Skip constructing Visualizer and LocalVisBackend artifacts.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the final diagnostic summary as JSON instead of text.",
    )
    return parser.parse_args()


def import_runtime() -> Dict[str, Any]:
    try:
        import mmengine
        from mmengine.config import Config
        from mmengine.device import get_device
        from mmengine.dist import get_dist_info, is_distributed
        from mmengine.logging import MMLogger, MessageHub, print_log
        from mmengine.utils.dl_utils import collect_env
        from mmengine.visualization import Visualizer
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise RuntimeError(
            "Failed to import MMEngine runtime utilities. If running from a "
            "source checkout, ensure the package dependencies are installed "
            "or run this script from an environment where the public "
            "mmengine distribution imports successfully."
        ) from exc

    return {
        "mmengine": mmengine,
        "Config": Config,
        "get_device": get_device,
        "get_dist_info": get_dist_info,
        "is_distributed": is_distributed,
        "MMLogger": MMLogger,
        "MessageHub": MessageHub,
        "print_log": print_log,
        "collect_env": collect_env,
        "Visualizer": Visualizer,
    }


def run_visualizer_check(api: Dict[str, Any], work_dir: Path) -> Dict[str, Any]:
    import numpy as np

    Config = api["Config"]
    Visualizer = api["Visualizer"]

    work_dir.mkdir(parents=True, exist_ok=True)
    visualizer = Visualizer(
        name="runtime-env-check",
        vis_backends=[dict(type="LocalVisBackend")],
        save_dir=str(work_dir),
    )
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    image[:, :, 1] = 255
    visualizer.add_scalar("runtime/check_scalar", 1.0, step=0)
    visualizer.add_scalars({"runtime/check_accuracy": 1.0}, step=0)
    visualizer.add_image("runtime_check_image", image, step=0)
    visualizer.add_config(Config(dict(runtime_env_check=True)))
    visualizer.close()

    vis_data_dir = work_dir / "vis_data"
    files = sorted(path.relative_to(work_dir).as_posix() for path in vis_data_dir.rglob("*") if path.is_file())
    return {"work_dir": str(work_dir), "files": files}


def main() -> int:
    args = parse_args()
    summary: Dict[str, Any] = {"ok": True, "checks": {}}

    try:
        api = import_runtime()
    except RuntimeError as exc:
        summary["ok"] = False
        summary["error"] = str(exc)
        if args.json:
            print(json.dumps(summary, indent=2, sort_keys=True))
        else:
            _status("mmengine import", False, str(exc))
        return 2

    mmengine = api["mmengine"]
    summary["checks"]["version"] = getattr(mmengine, "__version__", "unknown")

    logger = api["MMLogger"].get_instance("runtime-env-check", log_level="INFO")
    api["print_log"]("MMEngine runtime_env_check logger is available.", logger=logger)

    message_hub = api["MessageHub"].get_instance("runtime-env-check")
    message_hub.update_scalar("runtime/check_scalar", 1.0)
    message_hub.update_info("runtime/check_status", "ok")
    summary["checks"]["message_hub"] = {
        "scalar_keys": list(message_hub.log_scalars.keys()),
        "status": message_hub.get_info("runtime/check_status"),
    }

    rank, world_size = api["get_dist_info"]()
    summary["checks"]["distributed"] = {
        "initialized": bool(api["is_distributed"]()),
        "rank": rank,
        "world_size": world_size,
    }
    summary["checks"]["device"] = api["get_device"]()

    try:
        env = api["collect_env"]()
        summary["checks"]["environment"] = {
            key: env.get(key)
            for key in ("sys.platform", "Python", "PyTorch", "CUDA available", "MMEngine")
            if key in env
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        summary["checks"]["environment_error"] = str(exc)

    temp_dir = None
    if not args.skip_visualizer:
        try:
            if args.work_dir is None:
                temp_dir = tempfile.TemporaryDirectory(prefix="mmengine-runtime-check-")
                work_dir = Path(temp_dir.name)
            else:
                work_dir = args.work_dir
            summary["checks"]["visualizer"] = run_visualizer_check(api, work_dir)
        except Exception as exc:  # pragma: no cover - diagnostic path
            summary["ok"] = False
            summary["checks"]["visualizer_error"] = str(exc)
        finally:
            if temp_dir is not None:
                temp_dir.cleanup()

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True, default=_json_default))
    else:
        _status("mmengine import", True, f"version {summary['checks']['version']}")
        _status("message hub", True, ", ".join(summary["checks"]["message_hub"]["scalar_keys"]))
        dist = summary["checks"]["distributed"]
        _status(
            "distributed",
            True,
            f"initialized={dist['initialized']} rank={dist['rank']} world_size={dist['world_size']}",
        )
        _status("device", True, str(summary["checks"]["device"]))
        if "environment" in summary["checks"]:
            _status("collect_env", True, json.dumps(summary["checks"]["environment"], default=_json_default))
        else:
            _status("collect_env", False, summary["checks"].get("environment_error", "unknown"))
        if "visualizer" in summary["checks"]:
            visualizer = summary["checks"]["visualizer"]
            _status("local visualizer", True, f"wrote {len(visualizer['files'])} files under {visualizer['work_dir']}")
        elif "visualizer_error" in summary["checks"]:
            _status("local visualizer", False, summary["checks"]["visualizer_error"])

    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
