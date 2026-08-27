#!/usr/bin/env python3
"""Safe, tiny SunPy map constructor and headless visualization smoke check."""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord


def build_map():
    from sunpy.coordinates import frames
    from sunpy.map import Map, make_fitswcs_header

    data = np.arange(80, dtype=float).reshape(8, 10)
    reference = SkyCoord(
        0 * u.arcsec,
        0 * u.arcsec,
        frame=frames.Helioprojective,
        obstime="2020-01-01",
        observer="earth",
    )
    header = make_fitswcs_header(
        data,
        reference,
        scale=(2, 2) * u.arcsec / u.pixel,
        instrument="synthetic-smoke",
        wavelength=171 * u.angstrom,
    )
    return Map(data, header), reference


def run_check(output: Path | None = None) -> None:
    # Importing matplotlib before selecting a backend is intentional only when
    # the caller has already selected MPLBACKEND in the environment.  The
    # command line help remains usable without SunPy's optional plot imports.
    import sunpy.map

    m, reference = build_map()
    assert m.data.shape == (8, 10)
    assert m.wcs.array_shape == (8, 10)
    assert m.coordinate_frame is not None
    assert m.observer_coordinate is not None
    assert all(unit.is_equivalent(u.arcsec) for unit in m.spatial_units)

    world = m.pixel_to_world(4 * u.pixel, 3 * u.pixel)
    pixel = m.world_to_pixel(world)
    np.testing.assert_allclose([pixel.x.value, pixel.y.value], [4, 3], atol=1e-6)

    cut = m.submap([2, 2] * u.pixel, top_right=[7, 6] * u.pixel)
    assert cut.data.shape == (5, 6)
    small = cut.resample((3, 4) * u.pixel)
    assert small.data.shape == (4, 3)

    with tempfile.TemporaryDirectory(prefix="sunpy-map-smoke-") as tmp:
        fits_path = Path(tmp) / "tiny.fits"
        m.save(fits_path)
        restored = sunpy.map.Map(fits_path)
        assert restored.data.shape == m.data.shape
        assert list(restored.wcs.wcs.ctype) == list(m.wcs.wcs.ctype)

        target_header = sunpy.map.make_fitswcs_header(
            (6, 7),
            reference,
            reference_pixel=(3, 2) * u.pixel,
            scale=(3, 3) * u.arcsec / u.pixel,
        )
        try:
            projected, footprint = m.reproject_to(
                target_header, return_footprint=True
            )
        except ImportError as exc:
            projected = None
            print(f"reprojection skipped (optional dependency): {exc}")
        if projected is not None:
            assert projected.data.shape == (6, 7)
            assert footprint.shape == (6, 7)
            assert np.nanmin(footprint) >= 0
            assert np.nanmax(footprint) <= 1

        figure_path = Path(output) if output else Path(tmp) / "tiny.png"
        import matplotlib.pyplot as plt

        fig = plt.figure(figsize=(4, 3))
        ax = fig.add_subplot(projection=m)
        m.plot(axes=ax, clip_interval=(1, 99) * u.percent)
        m.draw_grid(axes=ax, grid_spacing=30 * u.deg)
        m.draw_limb(axes=ax, resolution=32)
        fig.savefig(figure_path, dpi=100)
        plt.close(fig)
        assert figure_path.exists() and figure_path.stat().st_size > 0

    print("map smoke passed: constructor, WCS round trip, crop/resample, FITS, plot")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="run the tiny in-memory smoke check"
    )
    parser.add_argument(
        "--output", type=Path, help="optional PNG path for the headless plot"
    )
    args = parser.parse_args()
    if not args.check:
        parser.print_help()
        return 0
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
    run_check(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
