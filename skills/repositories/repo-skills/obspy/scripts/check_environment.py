#!/usr/bin/env python3
"""Run a safe, read-only ObsPy installation and capability check.

The check uses synthetic data, shipped TauP models, a headless plot, and CLI
help. It never contacts network services, uses credentials, writes to the
current directory, or modifies the installed environment.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-plot", action="store_true",
        help="Skip the Matplotlib file-output smoke check.",
    )
    parser.add_argument(
        "--skip-cli", action="store_true",
        help="Skip console-script --help checks.",
    )
    args = parser.parse_args()

    import numpy as np
    import obspy
    from obspy import Stream, Trace, UTCDateTime
    from obspy.taup import TauPyModel

    print("obspy:", obspy.__version__)
    print("python:", sys.version.split()[0])
    trace = Trace(data=np.arange(32, dtype=np.float64))
    trace.stats.starttime = UTCDateTime("2020-01-01T00:00:00Z")
    trace.stats.sampling_rate = 8.0
    stream = Stream([trace])
    assert stream[0].stats.npts == 32

    native = {}
    for label, module_name, attr in (
        ("signal", "obspy.signal.headers", "clibsignal"),
        ("evresp", "obspy.signal.headers", "clibevresp"),
        ("mseed", "obspy.io.mseed.headers", "clibmseed"),
    ):
        try:
            module = __import__(module_name, fromlist=[attr])
            native[label] = bool(getattr(module, attr))
        except (ImportError, OSError, AttributeError) as exc:
            raise RuntimeError(f"native extension {label} unavailable: {exc}")
    print("native_extensions:", native)

    arrivals = TauPyModel("iasp91").get_travel_times(
        source_depth_in_km=55.0, distance_in_degree=67.0, phase_list=["P"]
    )
    assert arrivals and arrivals[0].name == "P"
    print("taup_P_seconds:", round(arrivals[0].time, 3))

    if not args.skip_plot:
        os.environ.setdefault("MPLBACKEND", "Agg")
        with tempfile.TemporaryDirectory(prefix="obspy-environment-") as tmp:
            output = Path(tmp) / "waveform.png"
            stream.plot(outfile=str(output), show=False)
            assert output.is_file() and output.stat().st_size > 0
            print("headless_plot_bytes:", output.stat().st_size)

    if not args.skip_cli:
        commands = ("obspy-print", "obspy-flinn-engdahl", "obspy-plot")
        for command in commands:
            completed = subprocess.run(
                [command, "--help"], capture_output=True, text=True, timeout=20
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    f"{command} --help failed ({completed.returncode}): "
                    f"{completed.stderr.strip()}"
                )
            print(f"{command}: help ok")

    print("ObsPy environment check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
