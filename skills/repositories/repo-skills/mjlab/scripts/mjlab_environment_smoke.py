from __future__ import annotations

import argparse
import importlib.metadata as metadata
import json
from typing import Any


def _task_summary() -> list[str]:
  import mjlab.tasks  # noqa: F401  # populate registry
  from mjlab.tasks.registry import list_tasks

  return list_tasks()


def _cuda_summary() -> dict[str, Any]:
  try:
    import torch
  except Exception as exc:  # pragma: no cover - defensive smoke helper
    return {"torch_imported": False, "error": repr(exc)}

  result: dict[str, Any] = {
    "torch_imported": True,
    "torch_version": getattr(torch, "__version__", None),
    "torch_cuda_version": getattr(torch.version, "cuda", None),
    "cuda_available": bool(torch.cuda.is_available()),
    "device_count": int(torch.cuda.device_count()),
  }
  if torch.cuda.is_available():
    try:
      tensor = torch.empty((1,), device="cuda")
      result.update(
        {
          "device0_name": torch.cuda.get_device_name(0),
          "device0_capability": torch.cuda.get_device_capability(0),
          "allocation_device": str(tensor.device),
        }
      )
    except Exception as exc:  # pragma: no cover - defensive smoke helper
      result["allocation_error"] = repr(exc)
  return result


def build_report() -> dict[str, Any]:
  import mujoco
  import mujoco_warp
  import warp
  import mjlab

  del mjlab
  tasks = _task_summary()
  return {
    "mjlab_version": metadata.version("mjlab"),
    "mujoco_version": mujoco.__version__,
    "mujoco_warp_imported": mujoco_warp.__name__,
    "warp_version": getattr(warp.config, "version", None),
    "task_count": len(tasks),
    "tasks": tasks,
    "cuda": _cuda_summary(),
  }


def main() -> int:
  parser = argparse.ArgumentParser(
    description="Smoke-check an installed mjlab environment and task registry."
  )
  parser.add_argument("--json", action="store_true", help="Emit JSON output.")
  args = parser.parse_args()

  report = build_report()
  if args.json:
    print(json.dumps(report, indent=2, sort_keys=True))
  else:
    print(f"mjlab: {report['mjlab_version']}")
    print(f"mujoco: {report['mujoco_version']}")
    print(f"mujoco_warp: {report['mujoco_warp_imported']}")
    print(f"warp: {report['warp_version']}")
    print(f"tasks: {report['task_count']}")
    for task in report["tasks"]:
      print(f"- {task}")
    cuda = report["cuda"]
    print(f"torch imported: {cuda.get('torch_imported')}")
    print(f"cuda available: {cuda.get('cuda_available')}")
    print(f"cuda device count: {cuda.get('device_count')}")
    if cuda.get("device0_name"):
      print(f"cuda device 0: {cuda['device0_name']} {cuda['device0_capability']}")
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
