#!/usr/bin/env python3
"""Inspect Krita AI Diffusion workspace enums and observable model properties."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path | None:
    for path in [start, *start.parents]:
        if (path / "ai_diffusion" / "__init__.py").exists():
            return path
    return None


def add_local_repo_to_path() -> None:
    for candidate in [Path.cwd(), Path(__file__).resolve().parent]:
        root = find_repo_root(candidate)
        if root is not None:
            root_text = str(root)
            if root_text not in sys.path:
                sys.path.insert(0, root_text)
            return

STATIC_ENUMS = {
    "Workspace": ["generation", "upscaling", "live", "animation", "custom"],
    "QueueMode": ["back", "front", "replace"],
    "ProgressKind": ["generation", "upload"],
    "ErrorKind": ["none", "plugin_error", "server_error", "insufficient_funds", "warning", "incompatible_lora", "validation_warning"],
    "JobKind": ["diffusion", "control_layer", "upscaling", "live_preview", "animation_batch", "animation_frame", "animation"],
    "JobState": ["queued", "executing", "finished", "cancelled"],
    "RegionLink": ["direct", "indirect", "any"],
    "ConnectionState": ["disconnected", "connecting", "connected", "error", "discover_models", "auth_missing", "auth_requesting", "auth_pending", "auth_error"],
    "ServerMode": ["undefined", "managed", "external", "cloud"],
    "ApplyBehavior": ["replace", "layer", "layer_active"],
    "ApplyRegionBehavior": ["none", "replace", "layer_group", "transparency_mask", "no_hide"],
    "WorkflowKind": ["generate", "inpaint", "refine", "refine_region", "upscale_simple", "upscale_tiled", "control_image", "custom"],
    "ControlMode": ["reference", "style", "composition", "face", "inpaint", "universal", "scribble", "line_art", "soft_edge", "canny_edge", "depth", "normal", "pose", "segmentation", "blur", "stencil", "hands"],
}

STATIC_PROPERTIES = {
    "DocumentModel": [
        {"name": "workspace", "persist": True, "default": "Workspace.generation"},
        {"name": "style", "persist": True, "default": "Styles.list().default"},
        {"name": "strength", "persist": True, "default": "1.0"},
        {"name": "region_only", "persist": True, "default": "False"},
        {"name": "edit_mode", "persist": True, "default": "False"},
        {"name": "batch_count", "persist": True, "default": "1"},
        {"name": "seed", "persist": True, "default": "0"},
        {"name": "fixed_seed", "persist": True, "default": "False"},
        {"name": "resolution_multiplier", "persist": True, "default": "1.0"},
        {"name": "queue_mode", "persist": True, "default": "QueueMode.back"},
        {"name": "translation_enabled", "persist": True, "default": "True"},
        {"name": "layer_count", "persist": True, "default": "4"},
        {"name": "progress_kind", "persist": False, "default": "ProgressKind.generation"},
        {"name": "progress", "persist": False, "default": "0.0"},
        {"name": "error", "persist": False, "default": "no_error"},
    ],
    "UpscaleWorkspace": [
        {"name": "upscaler", "persist": True, "default": ""},
        {"name": "factor", "persist": True, "default": "2.0"},
        {"name": "use_diffusion", "persist": True, "default": "True"},
        {"name": "strength", "persist": True, "default": "0.3"},
        {"name": "unblur_strength", "persist": True, "default": "0.5"},
        {"name": "tile_overlap_mode", "persist": True, "default": "TileOverlapMode.auto"},
        {"name": "tile_overlap", "persist": True, "default": "48"},
        {"name": "use_prompt", "persist": True, "default": "False"},
        {"name": "can_generate", "persist": False, "default": "True"},
    ],
    "LiveWorkspace": [
        {"name": "is_active", "persist": False, "default": "False"},
        {"name": "is_recording", "persist": False, "default": "False"},
        {"name": "strength", "persist": True, "default": "0.3"},
        {"name": "has_result", "persist": False, "default": "False"},
    ],
    "AnimationWorkspace": [
        {"name": "sampling_quality", "persist": True, "default": "SamplingQuality.fast"},
        {"name": "target_layer", "persist": True, "default": "QUuid()"},
        {"name": "batch_mode", "persist": True, "default": "True"},
    ],
    "CustomWorkspace": [
        {"name": "workflow_id", "persist": False, "default": ""},
        {"name": "workflow_params", "persist": True, "default": "{}"},
        {"name": "mode", "persist": True, "default": "CustomGenerationMode.regular"},
        {"name": "is_live", "persist": False, "default": "False"},
        {"name": "has_result", "persist": False, "default": "False"},
        {"name": "outputs", "persist": False, "default": "{}"},
        {"name": "params_ui_height", "persist": True, "default": "100"},
        {"name": "validation_error", "persist": False, "default": ""},
    ],
}


def enum_members(cls):
    return list(cls.__members__.keys())


def live_data() -> dict:
    from PyQt5.QtCore import QCoreApplication

    if QCoreApplication.instance() is None:
        QCoreApplication([])
    import ai_diffusion
    from ai_diffusion.backend.api import WorkflowKind
    from ai_diffusion.backend.resources import ControlMode, version as resource_version
    from ai_diffusion.model.connection import ConnectionState
    from ai_diffusion.model.jobs import JobKind, JobState
    from ai_diffusion.model.model import ErrorKind, ProgressKind, QueueMode, Workspace
    from ai_diffusion.model.region import RegionLink
    from ai_diffusion.settings import ApplyBehavior, ApplyRegionBehavior, ServerMode

    return {
        "source": "import-live",
        "versions": {"ai_diffusion": ai_diffusion.__version__, "resource_catalog": resource_version},
        "enums": {
            "Workspace": enum_members(Workspace),
            "QueueMode": enum_members(QueueMode),
            "ProgressKind": enum_members(ProgressKind),
            "ErrorKind": enum_members(ErrorKind),
            "JobKind": enum_members(JobKind),
            "JobState": enum_members(JobState),
            "RegionLink": enum_members(RegionLink),
            "ConnectionState": enum_members(ConnectionState),
            "ServerMode": enum_members(ServerMode),
            "ApplyBehavior": enum_members(ApplyBehavior),
            "ApplyRegionBehavior": enum_members(ApplyRegionBehavior),
            "WorkflowKind": enum_members(WorkflowKind),
            "ControlMode": enum_members(ControlMode),
        },
        "observable_properties": STATIC_PROPERTIES,
    }


def static_data() -> dict:
    return {"source": "static-fallback", "enums": STATIC_ENUMS, "observable_properties": STATIC_PROPERTIES}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Inspect workspace enums and observable properties.")
    parser.add_argument("--static-only", action="store_true", help="Do not import ai_diffusion; print bundled static facts.")
    parser.add_argument("--import-live", action="store_true", help="Import ai_diffusion and compare live enum values.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    add_local_repo_to_path()

    if args.import_live and not args.static_only:
        data = live_data()
    else:
        data = static_data()

    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print(f"source: {data['source']}")
        if versions := data.get("versions"):
            print("versions: " + ", ".join(f"{k}={v}" for k, v in versions.items()))
        print("guidance:")
        print("  - Static mode performs no imports or writes.")
        print("  - Use --import-live only in a working package/test environment.")
        print("  - Set QT_QPA_PLATFORM=offscreen for headless import checks.")
        print("\nenums:")
        for name, values in data["enums"].items():
            print(f"  {name}: {', '.join(values)}")
        print("\nobservable properties:")
        for owner, props in data["observable_properties"].items():
            print(f"  {owner}:")
            for prop in props:
                state = "persist" if prop["persist"] else "transient"
                print(f"    - {prop['name']} ({state}, default={prop['default']!r})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
