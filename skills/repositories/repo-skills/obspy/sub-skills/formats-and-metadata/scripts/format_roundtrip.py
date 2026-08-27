#!/usr/bin/env python3
"""Run deterministic local ObsPy format round trips.

Creates a fresh output directory, writes a tiny waveform as MiniSEED and ASCII,
and optionally writes minimal QuakeML and StationXML objects. It never contacts
network services and refuses to reuse a non-empty output directory.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("obspy-format-smoke"),
        help="New or empty directory for generated files.",
    )
    parser.add_argument(
        "--metadata", action="store_true",
        help="Also round-trip minimal QuakeML and StationXML objects.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit(f"Refusing non-empty output directory: {args.output_dir}")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    from obspy import Stream, Trace, UTCDateTime, read, read_events, read_inventory
    from obspy.core.event import Catalog, Event, Magnitude, Origin
    from obspy.core.inventory import Channel, Inventory, Network, Site, Station

    start = UTCDateTime("2020-01-01T00:00:00Z")
    trace = Trace(
        data=np.arange(20, dtype=np.int32),
        header={"network": "XX", "station": "FMT", "location": "00",
                "channel": "BHZ", "starttime": start, "sampling_rate": 10.0},
    )
    stream = Stream([trace])
    mseed = args.output_dir / "waveform.mseed"
    ascii_path = args.output_dir / "waveform.ascii"
    stream.write(mseed, format="MSEED")
    stream.write(ascii_path, format="SLIST")
    for path, fmt in ((mseed, "MSEED"), (ascii_path, "SLIST")):
        recovered = read(path, format=fmt)
        assert len(recovered) == 1 and recovered[0].id == trace.id
        assert recovered[0].stats.npts == trace.stats.npts
    print("waveform round trips passed")

    if args.metadata:
        event_path = args.output_dir / "event.xml"
        event = Event(origins=[Origin(time=start, latitude=1.0, longitude=2.0,
                                      depth=3000.0)],
                      magnitudes=[Magnitude(mag=4.2, magnitude_type="Mw")])
        Catalog(events=[event]).write(event_path, format="QUAKEML", validate=True)
        assert len(read_events(event_path, format="QUAKEML")) == 1

        station_path = args.output_dir / "station.xml"
        channel = Channel(code="BHZ", location_code="00", latitude=1.0,
                          longitude=2.0, elevation=100.0, depth=0.0,
                          sample_rate=10.0)
        station = Station(code="FMT", latitude=1.0, longitude=2.0,
                          elevation=100.0, site=Site(name="Smoke"),
                          channels=[channel])
        inventory = Inventory(networks=[Network(code="XX", stations=[station])],
                              source="ObsPy format smoke")
        inventory.write(station_path, format="STATIONXML", validate=True)
        assert len(read_inventory(station_path, format="STATIONXML")) == 1
        print("event and inventory round trips passed")

    print(f"wrote {len(list(args.output_dir.iterdir()))} files in {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
