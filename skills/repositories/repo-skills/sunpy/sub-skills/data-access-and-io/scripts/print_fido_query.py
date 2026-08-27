#!/usr/bin/env python3
"""Print a local SunPy Fido query without contacting a provider.

This helper deliberately never calls Fido.search() or Fido.fetch(). It is safe
for reviewing query composition, client registration, and an offline test case.
"""
from __future__ import annotations

import argparse

import astropy.units as u
from sunpy.net import Fido, attrs as a


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Construct and print a SunPy Fido attrs query; never search or fetch."
    )
    parser.add_argument("--start", default="2020-01-01T00:00:00", help="ISO-like start time")
    parser.add_argument("--end", default="2020-01-01T00:01:00", help="ISO-like end time")
    parser.add_argument("--instrument", default="AIA", help="Instrument value, e.g. AIA or HMI")
    parser.add_argument(
        "--wavelength",
        type=float,
        nargs="+",
        default=[171.0, 193.0],
        metavar="ANGSTROM",
        help="One or more wavelengths; alternatives are combined with OR",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.wavelength:
        raise SystemExit("at least one --wavelength is required")

    time = a.Time(args.start, args.end)
    instrument = a.Instrument(args.instrument)
    wavelength_attrs = [a.Wavelength(value * u.angstrom) for value in args.wavelength]
    wavelengths = a.AttrOr(wavelength_attrs)
    query = time & instrument & wavelengths

    print("network_called: false")
    print(f"registered_clients: {len(Fido.registry)}")
    print("query:")
    print(query)
    print("next_step: pass this query to Fido.search(query) only after network approval")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
