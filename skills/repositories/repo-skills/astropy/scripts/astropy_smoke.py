#!/usr/bin/env python3
"""Self-contained Astropy API smoke checks for generated repo-skill users.

The script uses only the installed ``astropy`` package and temporary files. It
is intentionally small: it verifies representative routes, not the full test
suite.
"""

from __future__ import annotations

import argparse
import json
import math
import tempfile
from pathlib import Path

import numpy as np


def run_smoke() -> dict[str, object]:
    from astropy import units as u
    from astropy.convolution import Gaussian2DKernel, convolve
    from astropy.coordinates import SkyCoord
    from astropy.cosmology import Planck18
    from astropy.io import fits
    from astropy.modeling import fitting, models
    from astropy.nddata import NDData, StdDevUncertainty
    from astropy.stats import sigma_clip
    from astropy.table import QTable, Table
    from astropy.time import Time
    from astropy.timeseries import LombScargle
    from astropy.visualization import ImageNormalize, ZScaleInterval
    from astropy.wcs import WCS

    result: dict[str, object] = {}

    speed = (42 * u.km / u.s).to(u.m / u.s)
    assert speed.value == 42000
    result["units"] = str(speed.unit)

    c = SkyCoord(ra=10 * u.deg, dec=20 * u.deg, frame="icrs")
    assert math.isfinite(c.galactic.l.deg)
    t = Time("2000-01-01T00:00:00", scale="utc")
    assert round(t.jd, 1) == 2451544.5
    result["time_coordinates"] = {"jd": round(t.jd, 1), "gal_l_deg": round(c.galactic.l.deg, 3)}

    qtab = QTable({"wave": [500, 600] * u.nm, "flux": [1.2, 2.3] * u.Jy})
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "tiny.ecsv"
        qtab.write(path, format="ascii.ecsv")
        roundtrip = QTable.read(path, format="ascii.ecsv")
        assert roundtrip["wave"].unit == u.nm

        fits_path = Path(td) / "tiny.fits"
        fits.PrimaryHDU(np.arange(4, dtype=np.float32).reshape(2, 2)).writeto(fits_path)
        with fits.open(fits_path) as hdul:
            assert hdul[0].data.shape == (2, 2)
    result["tables_io"] = "ecsv-and-fits-roundtrip"

    header = fits.Header()
    header["NAXIS"] = 2
    header["CTYPE1"] = "RA---TAN"
    header["CTYPE2"] = "DEC--TAN"
    header["CRVAL1"] = 0.0
    header["CRVAL2"] = 0.0
    header["CRPIX1"] = 1.0
    header["CRPIX2"] = 1.0
    header["CDELT1"] = -0.1
    header["CDELT2"] = 0.1
    wcs = WCS(header)
    world = wcs.all_pix2world([[0, 0]], 0)
    pix = wcs.all_world2pix(world, 0)
    assert np.allclose(pix, [[0, 0]], atol=1e-6)
    nd = NDData(np.ones((2, 2)), unit=u.ct, uncertainty=StdDevUncertainty(np.ones((2, 2)) * 0.1), wcs=wcs)
    assert nd.unit == u.ct and nd.uncertainty is not None
    result["wcs_nddata"] = "roundtrip"

    image = np.arange(25, dtype=float).reshape(5, 5)
    norm = ImageNormalize(image, interval=ZScaleInterval())
    normalized = norm(image)
    assert np.isfinite(normalized).any()
    conv = convolve(np.ones((5, 5)), Gaussian2DKernel(1))
    assert conv.shape == (5, 5)
    result["visualization_convolution"] = "normalized-and-convolved"

    x = np.arange(6.0)
    y = 2 * x + 1
    fitted = fitting.LinearLSQFitter()(models.Linear1D(), x, y)
    assert abs(fitted.slope.value - 2) < 1e-12
    clipped = sigma_clip([1, 1, 100], sigma=1)
    assert clipped.mask.tolist() == [False, False, True]
    power = LombScargle([1, 2, 3] * u.day, [1, 0, 1]).power([1] / u.day)
    assert power.shape == (1,)
    result["modeling_stats_timeseries"] = "fit-clip-periodogram"

    assert Planck18.age(0).unit.is_equivalent(u.Gyr)
    assert Planck18.comoving_distance(1).unit.is_equivalent(u.Mpc)
    result["cosmology"] = {"age0_gyr": round(Planck18.age(0).value, 3)}

    # Table import included late to catch registry side effects without relying on repo tests.
    assert Table({"a": [1, 2]})["a"].tolist() == [1, 2]

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run self-contained Astropy API smoke checks.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    args = parser.parse_args()

    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
        print("astropy smoke: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
