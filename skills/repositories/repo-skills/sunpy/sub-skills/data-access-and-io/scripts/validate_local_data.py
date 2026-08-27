#!/usr/bin/env python3
"""Validate a local SunPy data file without network access.

With no path the command creates a tiny FITS fixture in a temporary directory.
It never follows URLs, downloads sample data, or invokes Fido. ASDF support is
optional and is reported as a skip when the extra is unavailable.
"""
from __future__ import annotations

import argparse
import gzip
import re
import tempfile
from pathlib import Path

import numpy as np
from astropy.io import fits


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a local solar-data file and optionally run a tiny round trip."
    )
    parser.add_argument("path", nargs="?", type=Path, help="local file; omitted creates a tiny FITS fixture")
    parser.add_argument(
        "--header-only", action="store_true", help="inspect headers without constructing a Map"
    )
    parser.add_argument(
        "--roundtrip", choices=("fits", "asdf"), help="round-trip the generated or supplied Map"
    )
    return parser


def content_kind(path: Path) -> str:
    raw = path.read_bytes()[:80]
    if raw.startswith(b"#ASDF"):
        return "asdf"
    if raw[:3] == b"\x1f\x8b\x08":
        try:
            raw = gzip.open(path, "rb").read(80)
        except OSError:
            return "gzip/invalid"
    if re.match(rb"[A-Z0-9_ ]{1,8}=", raw) or raw.startswith(b"SIMPLE"):
        return "fits"
    if raw.startswith((b"\x00\x00\x00\x0cjP",)):
        return "jp2"
    return "unknown"


def make_fixture(directory: Path) -> Path:
    path = directory / "tiny-sunpy.fits"
    data = np.arange(12, dtype=np.float32).reshape(3, 4)
    header = fits.Header()
    header["SIMPLE"] = True
    header["BITPIX"] = -32
    header["NAXIS"] = 2
    header["NAXIS1"] = data.shape[1]
    header["NAXIS2"] = data.shape[0]
    header["CTYPE1"] = "HPLN-TAN"
    header["CTYPE2"] = "HPLT-TAN"
    header["CUNIT1"] = "arcsec"
    header["CUNIT2"] = "arcsec"
    header["CRPIX1"] = 2.5
    header["CRPIX2"] = 2.0
    header["CRVAL1"] = 0.0
    header["CRVAL2"] = 0.0
    header["CDELT1"] = 1.0
    header["CDELT2"] = 1.0
    header["DATE-OBS"] = "2020-01-01T00:00:00"
    header["HGLN_OBS"] = 0.0
    header["HGLT_OBS"] = 0.0
    header["DSUN_OBS"] = 1.496e11
    fits.PrimaryHDU(data=data, header=header).writeto(path)
    return path


def inspect_fits(path: Path, header_only: bool) -> object:
    with fits.open(path, memmap=False) as hdul:
        print(f"hdu_count: {len(hdul)}")
        shapes = []
        for index, hdu in enumerate(hdul):
            shape = None if hdu.data is None else tuple(hdu.data.shape)
            shapes.append(shape)
            print(f"hdu[{index}].shape: {shape}")
            print(f"hdu[{index}].keys: {list(hdu.header)[:10]}")
        if header_only:
            return None
    if not any(shape is not None and len(shape) >= 2 for shape in shapes):
        raise ValueError("FITS is readable but contains no 2-D HDU suitable for a Map")
    return shapes


def inspect_path(path: Path, header_only: bool):
    if not path.is_file():
        raise FileNotFoundError(path)
    kind = content_kind(path)
    print(f"path: {path}")
    print(f"content_kind: {kind}")
    suffix = path.suffix.lower().lstrip(".") or "<none>"
    print(f"suffix: {suffix}")
    if kind == "fits":
        inspect_fits(path, header_only)
        if not header_only:
            from sunpy.map import Map
            loaded = Map(path)
            print(f"map_type: {type(loaded).__name__}")
            print(f"map_shape: {tuple(loaded.data.shape)}")
    elif kind == "asdf" or suffix == "asdf":
        try:
            import asdf  # noqa: F401
        except ImportError:
            print("optional: ASDF reader unavailable; install sunpy[asdf]")
            return
        if not header_only:
            from sunpy.map import Map
            loaded = Map(path)
            print(f"map_type: {type(loaded).__name__}")
            print(f"map_shape: {tuple(loaded.data.shape)}")
    elif suffix in {"srs", "txt"}:
        from sunpy.io.special.srs import read_srs
        table = read_srs(path)
        print(f"table_type: {type(table).__name__}")
        print(f"table_columns: {table.colnames}")
        print(f"table_rows: {len(table)}")
    elif suffix == "genx":
        from sunpy.io.special.genx import read_genx
        result = read_genx(path)
        print(f"genx_type: {type(result).__name__}")
        print(f"genx_keys: {list(result)[:10]}")
    elif suffix in {"fz", "f0"}:
        from sunpy.io import ana
        pairs = ana.read(path)
        print(f"ana_pairs: {len(pairs)}")
        print(f"ana_shape: {tuple(pairs[0][0].shape)}")
    else:
        raise ValueError("unsupported or unrecognized local format; inspect bytes and suffix")


def roundtrip(kind: str, directory: Path):
    source = make_fixture(directory)
    from sunpy.map import Map

    loaded = Map(source)
    destination = directory / f"roundtrip.{kind}"
    if kind == "fits":
        loaded.save(destination)
    else:
        try:
            import asdf  # noqa: F401
        except ImportError:
            print("roundtrip: SKIP (install sunpy[asdf] for ASDF)")
            return
        loaded.save(destination)
    reloaded = Map(destination)
    if reloaded.data.shape != loaded.data.shape:
        raise AssertionError("roundtrip changed the data shape")
    print(f"roundtrip: {kind}")
    print(f"roundtrip_path: {destination.name}")
    print(f"roundtrip_shape: {tuple(reloaded.data.shape)}")


def main() -> int:
    args = build_parser().parse_args()
    with tempfile.TemporaryDirectory(prefix="sunpy-io-check-") as temp:
        directory = Path(temp)
        if args.roundtrip:
            roundtrip(args.roundtrip, directory)
            return 0
        path = args.path or make_fixture(directory)
        inspect_path(path, args.header_only)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
