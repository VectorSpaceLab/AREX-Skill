#!/usr/bin/env python3
"""Probe MNE-Python plotting/report backends without requiring GUI deps.

The script is intentionally safe for headless automation: it defaults to the
Matplotlib Agg backend, creates a tiny synthetic EEG topomap with show=False
when MNE is importable, and reports optional 2D/3D dependency availability by
import-spec lookup rather than importing heavy GUI stacks.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any


def _module_info(module_name: str, distribution: str | None = None) -> dict[str, Any]:
    distribution = distribution or module_name
    found = importlib.util.find_spec(module_name) is not None
    version = None
    if found:
        try:
            version = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            try:
                version = importlib.metadata.version(module_name)
            except importlib.metadata.PackageNotFoundError:
                version = "unknown"
    return {"module": module_name, "distribution": distribution, "found": found, "version": version}


def _display_hints() -> dict[str, Any]:
    keys = ("DISPLAY", "WAYLAND_DISPLAY", "MPLBACKEND", "QT_QPA_PLATFORM")
    return {key: bool(os.environ.get(key)) for key in keys}


def _make_topomap(output: Path | None, report_output: Path | None) -> dict[str, Any]:
    import numpy as np
    import matplotlib.pyplot as plt
    import mne

    ch_names = ["Fp1", "Fp2", "C3", "C4", "O1", "O2"]
    info = mne.create_info(ch_names=ch_names, sfreq=100.0, ch_types="eeg")
    info.set_montage("standard_1020")
    data = np.linspace(-1.0, 1.0, len(ch_names))

    im, cn = mne.viz.plot_topomap(
        data,
        info,
        contours=0,
        res=16,
        sensors=True,
        show=False,
    )
    fig = im.axes.figure
    fig.canvas.draw()

    result: dict[str, Any] = {
        "created": True,
        "figure_axes": len(fig.axes),
        "has_image": bool(fig.axes and fig.axes[0].images),
        "has_collections": bool(fig.axes and fig.axes[0].collections),
    }

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=100, bbox_inches="tight")
        result["saved_figure"] = str(output)
        result["saved_figure_bytes"] = output.stat().st_size

    if report_output is not None:
        report_output.parent.mkdir(parents=True, exist_ok=True)
        report = mne.Report(title="MNE plotting backend probe", image_format="png")
        report.add_figure(fig, title="Synthetic EEG topomap", tags=("probe", "topomap"))
        report.save(report_output, open_browser=False, overwrite=True)
        result["saved_report"] = str(report_output)
        result["saved_report_bytes"] = report_output.stat().st_size

    plt.close(fig)
    return result


def _format_text(result: dict[str, Any]) -> str:
    lines = []
    lines.append(f"status: {result['status']}")
    lines.append(f"python: {result['python']}")
    lines.append(f"display_hints: {result['display_hints']}")
    if result.get("matplotlib"):
        lines.append(f"matplotlib: {result['matplotlib']}")
    if result.get("mne"):
        lines.append(f"mne: {result['mne']}")
    lines.append("optional_dependencies:")
    for item in result["optional_dependencies"]:
        mark = "yes" if item["found"] else "no"
        version = f" {item['version']}" if item.get("version") else ""
        lines.append(f"  - {item['module']} ({item['distribution']}): {mark}{version}")
    if result.get("topomap"):
        lines.append(f"topomap: {result['topomap']}")
    if result.get("errors"):
        lines.append("errors:")
        for error in result["errors"]:
            lines.append(f"  - {error}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", default="Agg", help="Matplotlib backend to force before importing pyplot (default: Agg).")
    parser.add_argument("--output", type=Path, help="Optional path for a synthetic topomap PNG/SVG/etc.")
    parser.add_argument("--report-output", type=Path, help="Optional path for an HTML report containing the synthetic topomap.")
    parser.add_argument("--skip-topomap", action="store_true", help="Only report imports/dependencies; do not create a topomap.")
    parser.add_argument("--format", choices=("json", "text"), default="json", help="Output format (default: json).")
    args = parser.parse_args(argv)

    os.environ.setdefault("MPLBACKEND", args.backend)

    result: dict[str, Any] = {
        "status": "ok",
        "python": sys.version.split()[0],
        "display_hints": _display_hints(),
        "optional_dependencies": [
            _module_info("mne_qt_browser", "mne-qt-browser"),
            _module_info("qtpy"),
            _module_info("PySide6"),
            _module_info("PyQt6"),
            _module_info("pyvista"),
            _module_info("pyvistaqt"),
            _module_info("vtk"),
            _module_info("ipywidgets"),
            _module_info("ipympl"),
            _module_info("trame"),
            _module_info("trame_pyvista", "trame-pyvista"),
            _module_info("trame_vtk", "trame-vtk"),
            _module_info("trame_vuetify", "trame-vuetify"),
            _module_info("PIL", "Pillow"),
        ],
        "errors": [],
    }

    try:
        import matplotlib

        matplotlib.use(args.backend, force=True)
        result["matplotlib"] = {"version": matplotlib.__version__, "backend": matplotlib.get_backend()}
    except Exception as exc:  # pragma: no cover - environment-dependent
        result["status"] = "failed"
        result["errors"].append(f"matplotlib import/backend failed: {type(exc).__name__}: {exc}")

    try:
        import mne

        result["mne"] = {"version": getattr(mne, "__version__", "unknown")}
    except Exception as exc:  # pragma: no cover - environment-dependent
        result["status"] = "failed"
        result["errors"].append(f"mne import failed: {type(exc).__name__}: {exc}")

    if not args.skip_topomap and result.get("mne") and result.get("matplotlib"):
        try:
            result["topomap"] = _make_topomap(args.output, args.report_output)
        except Exception as exc:  # pragma: no cover - environment-dependent
            result["status"] = "failed"
            result["errors"].append(f"topomap/report smoke failed: {type(exc).__name__}: {exc}")

    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(_format_text(result))

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
