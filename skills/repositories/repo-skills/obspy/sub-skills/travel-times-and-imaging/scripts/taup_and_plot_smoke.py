#!/usr/bin/env python3
"""Offline TauP, geodesy, and headless imaging smoke check.

The script uses only shipped TauP model data and deterministic synthetic
samples. It never contacts a service or downloads map data.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a small offline ObsPy TauP/geodesy/imaging check."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("obspy-imaging-smoke"),
        help="New or empty output directory for generated figures.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(
            f"Refusing non-empty output directory: {output_dir}. "
            "Choose a new directory."
        )
    output_dir.mkdir(parents=True, exist_ok=True)

    # Select a non-interactive backend before importing pyplot through ObsPy.
    os.environ.setdefault("MPLBACKEND", "Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    from obspy import Stream, Trace
    from obspy.geodetics import gps2dist_azimuth, locations2degrees
    from obspy.imaging.beachball import beachball
    from obspy.taup import TauPyModel

    model = TauPyModel(model="iasp91")
    arrivals = model.get_travel_times(
        source_depth_in_km=10.0,
        distance_in_degree=35.0,
        phase_list=["P", "S"],
    )
    if not arrivals or not any(arrival.name == "P" for arrival in arrivals):
        raise RuntimeError("Expected a P arrival from the shipped iasp91 model")
    print("arrivals:", [(a.name, round(a.time, 3)) for a in arrivals])

    rays = model.get_ray_paths(100.0, 40.0, phase_list=["P"])
    if not rays or rays[0].path is None or len(rays[0].path) < 2:
        raise RuntimeError("Expected sampled P ray-path points")
    fig, ax = plt.subplots()
    rays.plot_rays(plot_type="cartesian", show=False, ax=ax, legend=True)
    ray_file = output_dir / "ray-path.png"
    fig.savefig(ray_file, dpi=90)
    plt.close(fig)

    degree_distance = float(locations2degrees(0.0, 0.0, 0.0, 10.0))
    metre_distance, azimuth, backazimuth = gps2dist_azimuth(
        0.0, 0.0, 0.0, 10.0
    )
    if not 9.0 < degree_distance < 11.0 or metre_distance <= 0:
        raise RuntimeError("Unexpected geodetic distance")
    print(
        "geodesy:",
        round(degree_distance, 6),
        round(metre_distance, 3),
        round(azimuth, 3),
        round(backazimuth, 3),
    )

    samples = np.sin(np.linspace(0.0, 24.0 * np.pi, 2048))
    trace = Trace(data=samples)
    trace.stats.sampling_rate = 100.0
    stream = Stream([trace])
    waveform_file = output_dir / "waveform.png"
    spectrum_file = output_dir / "spectrogram.png"
    stream.plot(outfile=str(waveform_file), show=False)
    trace.spectrogram(
        samp_rate=trace.stats.sampling_rate,
        wlen=2.0,
        outfile=str(spectrum_file),
        show=False,
    )
    beach_file = output_dir / "beachball.png"
    beachball([150.0, 87.0, 1.0], outfile=str(beach_file))

    for path in (ray_file, waveform_file, spectrum_file, beach_file):
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"Expected non-empty output: {path}")
    try:
        from obspy.imaging.maps import HAS_CARTOPY
    except (ImportError, RuntimeError) as exc:
        print("cartopy: unavailable (optional):", exc)
    else:
        print("cartopy:", "available" if HAS_CARTOPY else "unavailable (optional)")
    print("wrote:", ", ".join(str(path) for path in sorted(output_dir.iterdir())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
