#!/usr/bin/env python3
"""Run deterministic, local smoke checks for the waveform-processing route.

The script creates synthetic data in a temporary directory, so it does not
need a checkout, network access, credentials, or persistent output paths.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np


def _trace(data, start, *, rate=10.0, channel="BHZ", dtype=None):
    from obspy import Trace

    array = np.asarray(data, dtype=dtype)
    return Trace(
        data=array,
        header={
            "network": "XX",
            "station": "SMOKE",
            "location": "00",
            "channel": channel,
            "starttime": start,
            "sampling_rate": rate,
        },
    )


def _assert_unmasked(stream):
    for trace in stream:
        assert not (
            np.ma.isMaskedArray(trace.data) and np.ma.is_masked(trace.data)
        ), f"masked data remain for {trace.id}"


def run() -> None:
    """Execute the local construction, processing, merge, and round-trip checks."""
    # Import at execution time so ``--help`` remains available in an environment
    # where the optional ObsPy runtime has not yet been installed.
    from obspy import Stream, Trace, UTCDateTime, read

    start = UTCDateTime("2020-01-01T00:00:00Z")

    # Construction and Stats invariants.
    source = Stream([_trace(np.arange(40), start, rate=10.0, dtype=np.int32)])
    trace = source[0]
    assert trace.stats.npts == 40
    assert trace.stats.endtime == start + 3.9
    assert trace.stats.delta == 0.1

    # A two-sample gap is retained as a mask under the conservative policy.
    left = _trace(np.arange(10), start, rate=10.0, dtype=np.int32)
    right = _trace(np.arange(10, 20), start + 1.2, rate=10.0, dtype=np.int32)
    merged = Stream([left, right])
    merged.merge(method=0, fill_value=None)
    assert len(merged) == 1
    assert np.ma.isMaskedArray(merged[0].data)
    assert np.count_nonzero(np.ma.getmaskarray(merged[0].data)) == 2

    # Explicit interpolation removes the mask and is distinguishable from 0.
    interpolated = Stream([
        _trace(np.arange(10), start, rate=10.0, dtype=np.int32),
        _trace(np.arange(10, 20), start + 1.2, rate=10.0, dtype=np.int32),
    ])
    interpolated.merge(method=0, fill_value="interpolate")
    assert not np.ma.is_masked(interpolated[0].data)
    assert interpolated[0].data[10] == 9
    assert interpolated[0].data[11] == 9

    # Processing is done on a deep copy and updates the audit trail.
    processed = source.copy()
    processed.detrend("demean")
    processed.taper(max_percentage=0.05, type="cosine")
    processed.filter("lowpass", freq=3.0, corners=2, zerophase=True)
    processed.normalize()
    assert processed[0].stats.npts == source[0].stats.npts
    assert processed[0].stats.processing
    assert np.max(np.abs(processed[0].data)) <= 1.0 + 1e-12
    np.testing.assert_array_equal(source[0].data, np.arange(40, dtype=np.int32))

    # Headless local MiniSEED write/reopen and UTC-bound read.
    with tempfile.TemporaryDirectory(prefix="obspy-waveform-smoke-") as directory:
        path = Path(directory) / "waveform.mseed"
        source.write(path, format="MSEED")
        recovered = read(path, format="MSEED")
        assert len(recovered) == 1
        got = recovered[0]
        assert got.id == trace.id
        assert got.stats.starttime == start
        assert got.stats.endtime == trace.stats.endtime
        assert got.stats.sampling_rate == trace.stats.sampling_rate
        assert got.stats.npts == trace.stats.npts
        np.testing.assert_array_equal(got.data, trace.data)

        bounded = read(
            path,
            format="MSEED",
            starttime=start + 0.15,
            endtime=start + 0.35,
            nearest_sample=False,
        )
        assert bounded[0].stats.starttime == start + 0.2
        assert bounded[0].stats.endtime == start + 0.3
        np.testing.assert_array_equal(bounded[0].data, np.array([2, 3]))

        try:
            read(path, format="NOT_A_REAL_FORMAT")
        except (TypeError, ValueError) as exc:
            assert "NOT_A_REAL_FORMAT" in str(exc)
        else:  # pragma: no cover - protects the malformed-hint contract
            raise AssertionError("malformed format hint was accepted")

    _assert_unmasked(source)
    print("waveform smoke checks passed")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic local ObsPy waveform smoke checks."
    )
    parser.parse_args()
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
