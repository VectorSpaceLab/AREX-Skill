#!/usr/bin/env python3
"""Probe the public Inference SDK WebRTC/HTTP surface.

This helper is safe to run from any working directory. It performs no network
calls and no device access. Its only purpose is to confirm that the SDK import
surface is available and to print the verified signatures that the bundled
references describe.

Example:
    python scripts/check_webrtc_surface.py
    python scripts/check_webrtc_surface.py --json
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from dataclasses import is_dataclass
from pathlib import Path
from typing import Any, Dict


def _format_signature(obj: Any) -> str:
    return f"{obj.__qualname__}{inspect.signature(obj)}"


def _maybe_add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = str(Path(repo_root).expanduser().resolve())
    if root not in sys.path:
        sys.path.insert(0, root)


def _probe_surface(repo_root: str | None) -> Dict[str, Any]:
    _maybe_add_repo_root(repo_root)
    from inference_sdk import InferenceHTTPClient
    from inference_sdk.http.entities import InferenceConfiguration, HTTPClientMode
    from inference_sdk.http.errors import (
        APIKeyNotProvided,
        FeatureDeprecatedError,
        HTTPCallErrorError,
        HTTPClientError,
        InvalidModelIdentifier,
        InvalidParameterError,
        ModelNotSelectedError,
        ModelTaskTypeNotSupportedError,
        WrongClientModeError,
    )
    from inference_sdk.webrtc import (
        LocalStreamSource,
        MJPEGSource,
        ManualSource,
        RTSPSource,
        StreamConfig,
        VideoFileSource,
        VideoMetadata,
        WebRTCClient,
        WebRTCSession,
        WebcamSource,
    )
    from inference_sdk.webrtc.model_workflows import (
        apply_model_id_defaults,
        build_model_workflow,
        resolve_task_type,
    )

    return {
        "InferenceHTTPClient": {
            "init": _format_signature(InferenceHTTPClient.init),
            "ctor": _format_signature(InferenceHTTPClient),
            "infer": _format_signature(InferenceHTTPClient.infer),
            "infer_async": _format_signature(InferenceHTTPClient.infer_async),
            "run_workflow": _format_signature(InferenceHTTPClient.run_workflow),
            "infer_from_workflow": _format_signature(InferenceHTTPClient.infer_from_workflow),
            "start_inference_pipeline_with_workflow": _format_signature(
                InferenceHTTPClient.start_inference_pipeline_with_workflow
            ),
            "webrtc": _format_signature(InferenceHTTPClient.webrtc.fget),
        },
        "InferenceConfiguration": {
            "dataclass": is_dataclass(InferenceConfiguration),
            "ctor": _format_signature(InferenceConfiguration),
            "mode": f"{HTTPClientMode.V0.value} / {HTTPClientMode.V1.value}",
        },
        "WebRTCClient": {
            "ctor": _format_signature(WebRTCClient),
            "stream": _format_signature(WebRTCClient.stream),
        },
        "StreamConfig": {
            "ctor": _format_signature(StreamConfig),
            "fields": list(StreamConfig.__dataclass_fields__.keys()),
        },
        "WebRTC sources": {
            name: _format_signature(obj)
            for name, obj in [
                ("WebcamSource", WebcamSource),
                ("VideoFileSource", VideoFileSource),
                ("RTSPSource", RTSPSource),
                ("MJPEGSource", MJPEGSource),
                ("LocalStreamSource", LocalStreamSource),
                ("ManualSource", ManualSource),
            ]
        },
        "WebRTC session": {
            "ctor": _format_signature(WebRTCSession),
            "video_metadata": _format_signature(VideoMetadata),
            "video_mode": "workflow -> (frame, metadata), model_id -> (frame, data)",
        },
        "Model-id helpers": {
            "resolve_task_type": _format_signature(resolve_task_type),
            "build_model_workflow": _format_signature(build_model_workflow),
            "apply_model_id_defaults": _format_signature(apply_model_id_defaults),
        },
        "Public errors": [
            cls.__name__
            for cls in [
                HTTPClientError,
                HTTPCallErrorError,
                InvalidParameterError,
                WrongClientModeError,
                APIKeyNotProvided,
                ModelNotSelectedError,
                InvalidModelIdentifier,
                ModelTaskTypeNotSupportedError,
                FeatureDeprecatedError,
            ]
        ],
    }


def _print_report(report: Dict[str, Any]) -> None:
    print("InferenceHTTPClient")
    for key, value in report["InferenceHTTPClient"].items():
        print(f"  {key}: {value}")
    print()

    print("InferenceConfiguration")
    for key, value in report["InferenceConfiguration"].items():
        print(f"  {key}: {value}")
    print()

    print("WebRTCClient")
    for key, value in report["WebRTCClient"].items():
        print(f"  {key}: {value}")
    print()

    print("StreamConfig")
    print(f"  ctor: {report['StreamConfig']['ctor']}")
    print(f"  fields: {', '.join(report['StreamConfig']['fields'])}")
    print()

    print("WebRTC sources")
    for name, signature in report["WebRTC sources"].items():
        print(f"  {name}: {signature}")
    print()

    print("WebRTC session")
    for key, value in report["WebRTC session"].items():
        print(f"  {key}: {value}")
    print()

    print("Model-id helpers")
    for key, value in report["Model-id helpers"].items():
        print(f"  {key}: {value}")
    print()

    print("Public errors")
    for name in report["Public errors"]:
        print(f"  {name}")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="check_webrtc_surface.py",
        description="Probe the public Inference SDK WebRTC/HTTP surface.",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional local checkout root to add to PYTHONPATH before import.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON report instead of the default text summary.",
    )
    args = parser.parse_args()

    try:
        report = _probe_surface(args.repo_root)
    except ModuleNotFoundError as exc:
        print(
            f"Missing dependency while importing the SDK surface: {exc.name}",
            file=sys.stderr,
        )
        if exc.name == "dataclasses_json":
            print(
                "Install the base SDK dependency set before retrying. "
                "The HTTP entities need dataclasses_json.",
                file=sys.stderr,
            )
        elif exc.name in {"aiortc", "av"}:
            print(
                "Install the WebRTC extras: pip install inference-sdk[webrtc]",
                file=sys.stderr,
            )
        return 2
    except ImportError as exc:
        message = str(exc)
        print(f"Could not import the SDK surface: {message}", file=sys.stderr)
        if "WebRTC dependencies are not installed" in message:
            print(
                "Install the WebRTC extras: pip install inference-sdk[webrtc]",
                file=sys.stderr,
            )
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
