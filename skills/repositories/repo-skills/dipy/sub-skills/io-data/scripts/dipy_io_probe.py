#!/usr/bin/env python3
"""Safe Dipy IO probe for imports, signatures, gradients, and tractograms.

The probe performs no network access. It writes only to a temporary directory
unless --work-dir is provided.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
import tempfile
from pathlib import Path


def _import_dipy_io():
    try:
        import dipy
        import nibabel as nib
        import numpy as np
        from dipy.core.gradients import GradientTable, gradient_table
        from dipy.io.gradients import read_bvals_bvecs
        from dipy.io.image import load_nifti, save_nifti
        from dipy.io.peaks import load_pam, save_pam
        from dipy.io.stateful_tractogram import StatefulTractogram
        from dipy.io.streamline import load_tractogram, save_tractogram
        from dipy.io.utils import Origin, Space
    except Exception as exc:  # pragma: no cover - user environment diagnostics
        raise RuntimeError(
            "Could not import Dipy IO dependencies. Install Dipy with its base "
            f"runtime dependencies before using this probe. Original error: {exc}"
        ) from exc

    return {
        "dipy": dipy,
        "nib": nib,
        "np": np,
        "GradientTable": GradientTable,
        "gradient_table": gradient_table,
        "read_bvals_bvecs": read_bvals_bvecs,
        "load_nifti": load_nifti,
        "save_nifti": save_nifti,
        "load_pam": load_pam,
        "save_pam": save_pam,
        "Origin": Origin,
        "Space": Space,
        "StatefulTractogram": StatefulTractogram,
        "load_tractogram": load_tractogram,
        "save_tractogram": save_tractogram,
    }


def check_imports(mods):
    return {
        "dipy_version": getattr(mods["dipy"], "__version__", "unknown"),
        "numpy_version": getattr(mods["np"], "__version__", "unknown"),
        "nibabel_version": getattr(mods["nib"], "__version__", "unknown"),
    }


def check_signatures(mods):
    names = [
        "load_nifti",
        "save_nifti",
        "read_bvals_bvecs",
        "gradient_table",
        "GradientTable",
        "StatefulTractogram",
        "load_tractogram",
        "save_tractogram",
        "load_pam",
        "save_pam",
    ]
    return {name: str(inspect.signature(mods[name])) for name in names}


def tiny_gradient(mods):
    np = mods["np"]
    sqrt_half = np.sqrt(0.5)
    bvals = np.array([0, 1000, 1000, 1000, 1000, 1000, 1000], dtype=float)
    bvecs = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [sqrt_half, sqrt_half, 0.0],
            [sqrt_half, 0.0, sqrt_half],
            [0.0, sqrt_half, sqrt_half],
        ],
        dtype=float,
    )
    gtab = mods["gradient_table"](bvals, bvecs=bvecs, b0_threshold=50)
    non_b0_norms = np.linalg.norm(gtab.bvecs[~gtab.b0s_mask], axis=1)
    if not np.allclose(non_b0_norms, 1.0, atol=0.01):
        raise RuntimeError(f"Non-b0 b-vectors are not unit length: {non_b0_norms}")
    return {
        "bvals": int(len(gtab.bvals)),
        "bvecs_shape": list(gtab.bvecs.shape),
        "b0_count": int(gtab.b0s_mask.sum()),
        "non_b0_norm_min": float(non_b0_norms.min()),
        "non_b0_norm_max": float(non_b0_norms.max()),
    }


def tiny_tractogram(mods, work_dir=None):
    np = mods["np"]
    nib = mods["nib"]
    Space = mods["Space"]
    Origin = mods["Origin"]
    StatefulTractogram = mods["StatefulTractogram"]
    save_tractogram = mods["save_tractogram"]
    load_tractogram = mods["load_tractogram"]

    def run_in(directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        reference = nib.Nifti1Image(np.zeros((4, 4, 4), dtype="float32"), np.eye(4))
        streamlines = [
            np.array(
                [[0.5, 0.5, 0.5], [1.5, 1.5, 1.5], [2.0, 2.0, 2.0]],
                dtype="float32",
            )
        ]
        sft = StatefulTractogram(streamlines, reference, Space.RASMM, origin=Origin.NIFTI)
        before = {
            "bbox_valid": bool(sft.is_bbox_in_vox_valid()),
            "space": str(sft.space),
            "origin": str(sft.origin),
        }
        output_path = directory / "tiny.trk"
        save_tractogram(sft, output_path)
        loaded = load_tractogram(output_path, "same")
        if loaded is False:
            raise RuntimeError("Dipy returned False while reloading the tiny TRK file")
        return {
            "work_dir": str(directory if work_dir else "temporary-directory"),
            "file_name": output_path.name,
            "streamline_count": int(len(loaded)),
            "before_save": before,
            "after_load": {
                "bbox_valid": bool(loaded.is_bbox_in_vox_valid()),
                "space": str(loaded.space),
                "origin": str(loaded.origin),
            },
        }

    if work_dir is not None:
        return run_in(work_dir)

    with tempfile.TemporaryDirectory(prefix="dipy-io-probe-") as tmpdir:
        return run_in(tmpdir)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=(
            "Run safe Dipy IO checks: imports, public signatures, a tiny "
            "GradientTable validation, and a tiny tractogram round trip."
        )
    )
    parser.add_argument("--check-imports", action="store_true", help="Report Dipy, NumPy, and nibabel versions.")
    parser.add_argument("--check-signatures", action="store_true", help="Report main IO API signatures.")
    parser.add_argument("--tiny-gradient", action="store_true", help="Create and validate a seven-row GradientTable.")
    parser.add_argument("--tiny-tractogram", action="store_true", help="Create, save, and reload a one-streamline TRK.")
    parser.add_argument("--work-dir", type=Path, default=None, help="Optional directory for tiny tractogram output.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not any([args.check_imports, args.check_signatures, args.tiny_gradient, args.tiny_tractogram]):
        args.check_imports = True
        args.check_signatures = True
        args.tiny_gradient = True

    try:
        mods = _import_dipy_io()
        results = {"ok": True, "checks": {}}
        if args.check_imports:
            results["checks"]["imports"] = check_imports(mods)
        if args.check_signatures:
            results["checks"]["signatures"] = check_signatures(mods)
        if args.tiny_gradient:
            results["checks"]["tiny_gradient"] = tiny_gradient(mods)
        if args.tiny_tractogram:
            results["checks"]["tiny_tractogram"] = tiny_tractogram(mods, work_dir=args.work_dir)
    except Exception as exc:
        results = {"ok": False, "error": str(exc)}
        if args.json:
            print(json.dumps(results, indent=2, sort_keys=True))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(results, indent=2, sort_keys=True))
    else:
        print("Dipy IO probe: OK")
        for check_name, payload in results["checks"].items():
            print(f"\n[{check_name}]")
            for key, value in payload.items():
                print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
