#!/usr/bin/env python3
"""No-download PyWavelets smoke check.

This helper imports the installed `pywt` package, exercises representative
1D/2D/ND discrete transforms, coefficient packing, stationary transforms,
multiresolution analysis, continuous transforms, wavelet packets, and bundled
data accessors, then prints a short status report.

Optional:
- `--repo-root PATH` prepends a local checkout to `sys.path` before importing.
- `--json` prints structured output instead of the human-readable summary.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable


def _maybe_add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = Path(repo_root).expanduser().resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def _run_check(result: dict, name: str, fn: Callable[[], None]) -> None:
    try:
        fn()
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["checks"].append({"name": name, "status": "fail", "error": f"{type(exc).__name__}: {exc}"})
        result["errors"].append(f"{name}: {type(exc).__name__}: {exc}")
    else:
        result["checks"].append({"name": name, "status": "pass"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Optional checkout root to prepend to sys.path before importing.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    _maybe_add_repo_root(args.repo_root)

    result: dict = {
        "ok": False,
        "version": None,
        "checks": [],
        "errors": [],
    }

    try:
        import numpy as np
        import pywt
    except Exception as exc:  # pragma: no cover - diagnostic path
        result["errors"].append(f"import failed: {type(exc).__name__}: {exc}")
        _print_result(result, args.json)
        return 1

    result["version"] = getattr(pywt, "__version__", "unknown")

    def check_public_surface() -> None:
        expected = [
            "Wavelet",
            "ContinuousWavelet",
            "DiscreteContinuousWavelet",
            "Modes",
            "dwt",
            "idwt",
            "wavedec",
            "waverec",
            "dwt2",
            "idwt2",
            "dwtn",
            "idwtn",
            "wavedecn",
            "waverecn",
            "swt",
            "iswt",
            "swt2",
            "iswt2",
            "swtn",
            "iswtn",
            "mra",
            "mra2",
            "mran",
            "imra",
            "imra2",
            "imran",
            "coeffs_to_array",
            "array_to_coeffs",
            "ravel_coeffs",
            "unravel_coeffs",
            "wavedecn_size",
            "wavedecn_shapes",
            "fswavedecn",
            "fswaverecn",
            "threshold",
            "threshold_firm",
            "pad",
            "families",
            "wavelist",
            "cwt",
            "data",
        ]
        missing = [name for name in expected if not hasattr(pywt, name)]
        if missing:
            raise AssertionError(f"missing public names: {missing}")
        assert pywt.Modes.modes == [
            "zero",
            "constant",
            "symmetric",
            "periodic",
            "smooth",
            "periodization",
            "reflect",
            "antisymmetric",
            "antireflect",
        ]

    def check_dwt_roundtrip() -> None:
        x = np.array([3, 7, 1, 1, -2, 5, 4, 6], dtype=float)
        cA, cD = pywt.dwt(x, "db2")
        rec = pywt.idwt(cA, cD, "db2")
        assert np.allclose(rec, x)
        coeffs = pywt.wavedec(x, "db1", level=2)
        assert np.allclose(pywt.waverec(coeffs, "db1"), x)

    def check_multidim_and_pack() -> None:
        img = np.arange(16.0).reshape(4, 4)
        coeffs2 = pywt.wavedec2(img, "db1", level=1)
        assert np.allclose(pywt.waverec2(coeffs2, "db1"), img)
        coeffsn = pywt.wavedecn(img, "db1", level=1)
        arr, slices = pywt.coeffs_to_array(coeffsn)
        roundtrip = pywt.array_to_coeffs(arr, slices)
        assert np.allclose(pywt.waverecn(roundtrip, "db1"), img)
        rav, r_slices, r_shapes = pywt.ravel_coeffs(coeffsn)
        unraveled = pywt.unravel_coeffs(rav, r_slices, r_shapes)
        assert np.allclose(pywt.waverecn(unraveled, "db1"), img)

    def check_stationary_and_mra() -> None:
        x = np.arange(8.0)
        coeffs = pywt.swt(x, "db1", level=2, trim_approx=True)
        assert np.allclose(pywt.iswt(coeffs, "db1"), x)
        mra_coeffs = pywt.mra(x, "db1", transform="swt")
        assert np.allclose(pywt.imra(mra_coeffs), x)

    def check_fswavedecn() -> None:
        data = np.ones((4, 4))
        fs = pywt.fswavedecn(data, "haar", levels=1)
        assert fs.coeffs.shape == data.shape
        assert np.allclose(pywt.fswaverecn(fs), data)

    def check_cwt_and_wavelets() -> None:
        time, sst = pywt.data.nino()
        cwt, freqs = pywt.cwt(sst[:32], np.arange(1, 4), "morl", time[1] - time[0])
        assert cwt.shape == (3, 32)
        assert freqs.shape == (3,)
        assert "morl" in pywt.wavelist(kind="continuous")
        assert len(pywt.families()) > 0

    def check_packets() -> None:
        wp = pywt.WaveletPacket(np.arange(8.0), "db1")
        assert np.allclose(wp.reconstruct(), np.arange(8.0))
        wp2 = pywt.WaveletPacket2D(np.ones((4, 4)), "db1")
        assert np.allclose(wp2.reconstruct(), np.ones((4, 4)))
        wpn = pywt.WaveletPacketND(np.ones((4, 4, 4)), "db1")
        assert np.allclose(wpn.reconstruct(), np.ones((4, 4, 4)))

    def check_bundled_data() -> None:
        assert pywt.data.camera().shape == (512, 512)
        assert pywt.data.ascent().shape == (512, 512)
        assert pywt.data.aero().shape == (512, 512)
        assert pywt.data.ecg().shape == (1024,)
        time, sst = pywt.data.nino()
        assert time.shape == sst.shape == (264,)
        demo_names = pywt.data.demo_signal("list")
        assert "Doppler" in demo_names
        assert pywt.data.demo_signal("doppler", 32).shape == (32,)

    def check_threshold_and_pad() -> None:
        values = np.array([1.0, 2.0, 3.0])
        assert pywt.threshold(values, 2, "soft").shape == values.shape
        assert pywt.pad(values, 1, "symmetric").shape == (5,)

    _run_check(result, "public surface", check_public_surface)
    _run_check(result, "dwt roundtrip", check_dwt_roundtrip)
    _run_check(result, "multidim and coeff packing", check_multidim_and_pack)
    _run_check(result, "stationary and mra", check_stationary_and_mra)
    _run_check(result, "fully separable transform", check_fswavedecn)
    _run_check(result, "cwt and wavelets", check_cwt_and_wavelets)
    _run_check(result, "wavelet packets", check_packets)
    _run_check(result, "bundled data", check_bundled_data)
    _run_check(result, "threshold and pad", check_threshold_and_pad)

    result["ok"] = not result["errors"]
    _print_result(result, args.json)
    return 0 if result["ok"] else 1


def _print_result(result: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    print(f"pywt_version={result.get('version', 'unknown')}")
    for check in result.get("checks", []):
        if check["status"] == "pass":
            print(f"PASS {check['name']}")
        else:
            print(f"FAIL {check['name']}: {check['error']}")
    if result.get("errors"):
        print("errors:")
        for error in result["errors"]:
            print(f"- {error}")


if __name__ == "__main__":
    raise SystemExit(main())
