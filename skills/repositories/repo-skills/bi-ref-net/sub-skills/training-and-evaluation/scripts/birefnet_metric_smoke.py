#!/usr/bin/env python3
"""Create tiny BiRefNet mask fixtures and smoke-test evaluation.metrics.evaluator.

The helper is safe from arbitrary current working directories:
- it never imports source modules from the ambient cwd;
- it uses an explicit --repo-root when supplied, or infers the repo root from the
  bundled script location;
- it creates temporary masks only under a private temp directory.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple

import numpy as np
from PIL import Image

ALL_METRICS: List[str] = ["S", "MAE", "E", "F", "WF", "MBA", "BIoU", "MSE", "HCE"]
RESULT_NAMES: Tuple[str, ...] = ("E", "S", "F", "MAE", "MSE", "WF", "HCE", "MBA", "BIoU")
REQUIRED_MARKERS: Tuple[str, ...] = ("config.py", "train.py", os.path.join("evaluation", "metrics.py"))
DEFAULT_METRICS = "all"


def _scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    return value


def _format_number(value: Any) -> str:
    value = _scalar(value)
    if isinstance(value, (int, float)):
        return f"{value:.6g}"
    return str(value)


def summarize_array(array: Any) -> Dict[str, Any]:
    arr = np.asarray(array)
    summary: Dict[str, Any] = {
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
    }
    if arr.size:
        summary.update(
            {
                "min": _scalar(arr.min()),
                "max": _scalar(arr.max()),
                "mean": _scalar(arr.mean()),
            }
        )
    else:
        summary.update({"min": None, "max": None, "mean": None})
    return summary


def summarize_metric_value(value: Any) -> Any:
    if isinstance(value, dict):
        summary: Dict[str, Any] = {}
        if "adp" in value:
            summary["adp"] = summarize_metric_value(value["adp"])
        if "curve" in value:
            summary["curve"] = summarize_array(value["curve"])
        for key, subvalue in value.items():
            if key in {"adp", "curve"}:
                continue
            summary[key] = summarize_metric_value(subvalue)
        return summary
    if isinstance(value, np.ndarray):
        return summarize_array(value)
    if isinstance(value, np.generic):
        return value.item()
    return value


def summarize_result_tuple(result_tuple: Tuple[Any, ...]) -> Dict[str, Any]:
    return {name: summarize_metric_value(value) for name, value in zip(RESULT_NAMES, result_tuple)}


def compact_metric_line(value: Any) -> str:
    if isinstance(value, dict):
        parts: List[str] = []
        if "adp" in value:
            parts.append(f"adp={_format_number(value['adp'])}")
        if "curve" in value and isinstance(value["curve"], dict):
            curve = value["curve"]
            parts.append(f"curve_shape={curve['shape']}")
            parts.append(f"curve_min={_format_number(curve['min'])}")
            parts.append(f"curve_max={_format_number(curve['max'])}")
            if curve.get("mean") is not None:
                parts.append(f"curve_mean={_format_number(curve['mean'])}")
        for key in sorted(k for k in value.keys() if k not in {"adp", "curve"}):
            parts.append(f"{key}={compact_metric_line(value[key])}")
        return "; ".join(parts) if parts else "{}"
    return _format_number(value)


def parse_metrics(metric_spec: str) -> List[str]:
    metric_spec = metric_spec.strip()
    if metric_spec.lower() == "all":
        return list(ALL_METRICS)
    metrics = [item.strip() for item in metric_spec.split("+") if item.strip()]
    if not metrics:
        raise ValueError("at least one metric is required")
    unknown = [metric for metric in metrics if metric not in ALL_METRICS]
    if unknown:
        allowed = ", ".join(["all", "+".join(ALL_METRICS)])
        raise ValueError(f"unknown metric(s): {', '.join(unknown)}; allowed values: {allowed}")
    return metrics


def make_center_mask(height: int, width: int, margin: int) -> np.ndarray:
    mask = np.zeros((height, width), dtype=np.uint8)
    if height <= margin * 2 or width <= margin * 2:
        mask[:, :] = 255
    else:
        mask[margin : height - margin, margin : width - margin] = 255
    return mask


def write_mask(path: Path, mask: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(mask, mode="L").save(path)


def build_fixtures(tmp_root: Path) -> List[Dict[str, Any]]:
    gt_dir = tmp_root / "gt"
    pred_dir = tmp_root / "pred"
    specs = [
        {"name": "sample_0", "gt_shape": (8, 8), "gt_margin": 2, "pred_shape": (6, 6), "pred_margin": 1},
        {"name": "sample_1", "gt_shape": (9, 7), "gt_margin": 2, "pred_shape": (5, 4), "pred_margin": 1},
    ]
    fixtures: List[Dict[str, Any]] = []
    for spec in specs:
        gt_mask = make_center_mask(spec["gt_shape"][0], spec["gt_shape"][1], spec["gt_margin"])
        pred_mask = make_center_mask(spec["pred_shape"][0], spec["pred_shape"][1], spec["pred_margin"])
        gt_path = gt_dir / f"{spec['name']}.png"
        pred_path = pred_dir / f"{spec['name']}.png"
        write_mask(gt_path, gt_mask)
        write_mask(pred_path, pred_mask)
        fixtures.append(
            {
                "name": spec["name"],
                "gt_path": str(gt_path),
                "pred_path": str(pred_path),
                "gt_shape": list(spec["gt_shape"]),
                "pred_shape": list(spec["pred_shape"]),
                "gt_margin": spec["gt_margin"],
                "pred_margin": spec["pred_margin"],
            }
        )
    return fixtures


def validate_repo_root(repo_root: Path) -> Path:
    repo_root = repo_root.expanduser().resolve()
    if not repo_root.is_dir():
        raise FileNotFoundError(f"repo root does not exist or is not a directory: {repo_root}")
    missing = []
    for rel in REQUIRED_MARKERS:
        if not (repo_root / rel).is_file():
            missing.append(rel)
    if missing:
        raise FileNotFoundError(
            f"repo root is missing required BiRefNet files: {', '.join(missing)}"
        )
    return repo_root


def infer_repo_root_from_script() -> Path | None:
    script_dir = Path(__file__).resolve().parent
    for candidate in [script_dir, *script_dir.parents]:
        try:
            validated = validate_repo_root(candidate)
        except FileNotFoundError:
            continue
        else:
            return validated
    return None


@contextlib.contextmanager
def repo_import_context(repo_root: Path) -> Iterator[Path]:
    old_sys_path = list(sys.path)
    old_cwd = Path.cwd()
    try:
        sys.path.insert(0, str(repo_root))
        os.chdir(repo_root)
        yield repo_root
    finally:
        os.chdir(old_cwd)
        sys.path[:] = old_sys_path


def resolve_repo_root(explicit_repo_root: Path | None) -> Tuple[Path, str]:
    if explicit_repo_root is not None:
        return validate_repo_root(explicit_repo_root), "explicit"
    inferred = infer_repo_root_from_script()
    if inferred is None:
        raise FileNotFoundError(
            "could not infer the BiRefNet repo root from this script location; "
            "pass --repo-root <path-to-BiRefNet>"
        )
    return inferred, "inferred from script location"


def run_smoke(repo_root: Path, repo_root_source: str, metrics: List[str]) -> Dict[str, Any]:
    with repo_import_context(repo_root):
        try:
            from evaluation.metrics import evaluator  # type: ignore
        except Exception as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "unable to import evaluation.metrics from the supplied repo root; "
                f"original error: {type(exc).__name__}: {exc}; "
                "install the BiRefNet requirements and confirm the checkout root"
            ) from exc

        with tempfile.TemporaryDirectory(prefix="birefnet_metric_smoke_") as tmp_dir:
            fixture_root = Path(tmp_dir)
            fixtures = build_fixtures(fixture_root)
            gt_paths = [item["gt_path"] for item in fixtures]
            pred_paths = [item["pred_path"] for item in fixtures]
            result_tuple = evaluator(
                gt_paths=gt_paths,
                pred_paths=pred_paths,
                metrics=metrics,
                verbose=False,
                num_workers=1,
            )
            report = {
                "status": "ok",
                "repo_root": str(repo_root),
                "repo_root_source": repo_root_source,
                "metrics": metrics,
                "fixture_root": str(fixture_root),
                "fixtures": fixtures,
                "results": summarize_result_tuple(result_tuple),
                "note": "temporary fixtures were removed after the smoke run",
            }
    return report


def render_text_report(report: Dict[str, Any]) -> None:
    print("BiRefNet metric smoke")
    print(f"repo root: {report['repo_root']} ({report['repo_root_source']})")
    print(f"metrics: {'+'.join(report['metrics'])}")
    print(f"fixture root: {report['fixture_root']} (cleaned up after run)")
    print("fixtures:")
    for item in report["fixtures"]:
        print(
            f"  - {item['name']}: gt {item['gt_shape']} -> {item['gt_path']}; "
            f"pred {item['pred_shape']} -> {item['pred_path']}"
        )
    print("results:")
    for name in RESULT_NAMES:
        print(f"  - {name}: {compact_metric_line(report['results'][name])}")
    print("Tip: rerun with --json for machine-readable output.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create tiny BiRefNet mask fixtures and smoke-test evaluation.metrics.evaluator.",
        epilog="Example: python birefnet_metric_smoke.py --repo-root /path/to/BiRefNet --metrics all",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Explicit BiRefNet checkout root. If omitted, the script tries to infer it from its own location.",
    )
    parser.add_argument(
        "--metrics",
        type=str,
        default=DEFAULT_METRICS,
        help="Metric subset to pass to evaluation.metrics.evaluator. Use 'all' or a '+'-joined subset such as S+MAE+WF.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a machine-readable JSON report instead of text.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo_root, repo_root_source = resolve_repo_root(args.repo_root)
        metrics = parse_metrics(args.metrics)
        report = run_smoke(repo_root, repo_root_source, metrics)
    except Exception as exc:  # pragma: no cover - environment dependent
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, indent=2, sort_keys=True))
        else:
            print(f"BiRefNet metric smoke failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        render_text_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
