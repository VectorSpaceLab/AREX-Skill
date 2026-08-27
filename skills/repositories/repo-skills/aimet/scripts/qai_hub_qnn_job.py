#!/usr/bin/env python3
"""Submit an AIMET/QDQ ONNX model to Qualcomm AI Hub for QNN compile/profile.

Dry-run mode is dependency-free and is safe for planning. Real execution imports
`qai_hub`, uploads the model, compiles it for the selected device/runtime,
downloads the compiled artifact, profiles it, and can submit one inference job
from a NumPy NPZ input bundle.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qdq-model", required=True, help="ONNX QDQ model path, or AIMET-exported ONNX accepted by the target flow")
    parser.add_argument("--device", required=True, help="Qualcomm AI Hub device name")
    parser.add_argument("--model-name", default="aimet-qnn-model", help="Name for the Hub compile job")
    parser.add_argument("--compile-options", default="", help="Compile options string passed to AI Hub/QNN")
    parser.add_argument("--output-dir", default="qai_hub_artifacts", help="Local directory for downloaded compiled artifacts")
    parser.add_argument("--compiled-zip", default=None, help="Compiled zip path (default: output-dir/model-name_qnn.zip)")
    parser.add_argument("--input-npz", default=None, help="Optional NPZ containing named inference inputs; each array is wrapped as one sample unless already object/list-like")
    parser.add_argument("--save-output-npz", default=None, help="Optional NPZ path for downloaded inference outputs")
    parser.add_argument("--dry-run", action="store_true", help="Validate arguments and print the planned Hub operations without importing qai_hub")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    return parser.parse_args()


def require_file(path: str, label: str) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise SystemExit(f"{label} not found: {p}")
    return p


def latency_from_profile(profile: Any) -> float | None:
    if isinstance(profile, dict):
        us = (
            profile.get("execution_summary", {}).get("estimated_inference_time")
            or profile.get("inference_summary", {}).get("estimated_inference_time_us")
            or profile.get("latency_us")
        )
        if us is not None:
            try:
                return float(us) / 1000.0
            except Exception:
                return None
    summary = getattr(profile, "summary", None)
    if summary is not None:
        for attr, scale in (("latency_ms", 1.0), ("estimated_inference_time_us", 0.001)):
            if hasattr(summary, attr):
                try:
                    return float(getattr(summary, attr)) * scale
                except Exception:
                    return None
    return None


def npz_inputs(path: Path) -> dict[str, list[Any]]:
    import numpy as np

    data = np.load(path, allow_pickle=True)
    feeds: dict[str, list[Any]] = {}
    for name in data.files:
        arr = data[name]
        if arr.dtype == object:
            feeds[name] = [np.ascontiguousarray(x) for x in arr.tolist()]
        elif arr.ndim > 0 and arr.shape[0] > 1:
            feeds[name] = [np.ascontiguousarray(arr[i : i + 1]) for i in range(arr.shape[0])]
        else:
            feeds[name] = [np.ascontiguousarray(arr)]
    if not feeds:
        raise SystemExit(f"No arrays found in NPZ: {path}")
    return feeds


def save_outputs(path: Path, outputs: Any) -> None:
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(outputs, dict):
        converted = {}
        for name, value in outputs.items():
            if isinstance(value, list):
                converted[name] = np.asarray(value, dtype=object)
            else:
                converted[name] = np.asarray(value)
        np.savez(path, **converted)
    else:
        np.savez(path, output=np.asarray(outputs, dtype=object))


def print_or_json(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        for key, value in payload.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")


def main() -> int:
    args = parse_args()
    model_path = require_file(args.qdq_model, "QDQ/ONNX model")
    output_dir = Path(args.output_dir).expanduser().resolve()
    compiled_zip = Path(args.compiled_zip).expanduser().resolve() if args.compiled_zip else output_dir / f"{args.model_name}_qnn.zip"
    input_npz = require_file(args.input_npz, "input NPZ") if args.input_npz else None
    save_output_npz = Path(args.save_output_npz).expanduser().resolve() if args.save_output_npz else None

    plan = {
        "model": str(model_path),
        "device": args.device,
        "model_name": args.model_name,
        "compile_options": args.compile_options or "(Hub defaults)",
        "compiled_zip": str(compiled_zip),
        "input_npz": str(input_npz) if input_npz else None,
        "save_output_npz": str(save_output_npz) if save_output_npz else None,
    }

    if args.dry_run:
        plan["dry_run"] = True
        plan["credential_boundary"] = "real execution requires installed/authenticated qai_hub"
        print_or_json(plan, args.json)
        return 0

    try:
        import qai_hub as hub
    except Exception as exc:  # pragma: no cover - environment dependent
        raise SystemExit("qai_hub is required for real AI Hub execution; install/authenticate it or use --dry-run") from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    device = hub.Device(args.device)
    print(f"Submitting compile job for {model_path} on {args.device}...")
    compile_job = hub.submit_compile_job(
        model=str(model_path),
        device=device,
        name=args.model_name,
        options=args.compile_options or None,
    )
    target_model = compile_job.get_target_model()
    target_model.download(str(compiled_zip))

    print("Submitting profile job...")
    profile_job = hub.submit_profile_job(model=target_model, device=device)
    profile = profile_job.download_profile()
    latency_ms = latency_from_profile(profile)

    result: dict[str, Any] = {
        **plan,
        "compile_job_url": getattr(compile_job, "url", "") or "",
        "profile_job_url": getattr(profile_job, "url", "") or "",
        "latency_ms": latency_ms,
    }

    if input_npz is not None:
        print(f"Submitting inference job with inputs from {input_npz}...")
        feeds = npz_inputs(input_npz)
        inference_job = hub.submit_inference_job(model=target_model, device=device, inputs=feeds)
        outputs = inference_job.download_output_data()
        result["inference_job_url"] = getattr(inference_job, "url", "") or ""
        result["output_names"] = sorted(outputs.keys()) if isinstance(outputs, dict) else []
        if save_output_npz is not None:
            save_outputs(save_output_npz, outputs)
            result["saved_output_npz"] = str(save_output_npz)

    print_or_json(result, args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
