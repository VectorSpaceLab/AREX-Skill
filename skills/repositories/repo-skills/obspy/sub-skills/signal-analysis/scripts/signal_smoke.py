#!/usr/bin/env python3
"""Run a deterministic CPU-only ObsPy signal-processing smoke check.

The helper creates synthetic in-memory data and never accesses network,
credentials, external response files, or persistent output paths.
"""
from __future__ import annotations

import argparse

import numpy as np


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    from obspy import Stream, Trace, UTCDateTime
    from obspy.signal.cross_correlation import correlate
    from obspy.signal.trigger import (
        classic_sta_lta,
        recursive_sta_lta,
        trigger_onset,
    )

    rng = np.random.default_rng(7)
    n = 2000
    rate = 100.0
    data = 0.02 * rng.standard_normal(n)
    data[900:1050] += np.hanning(150) * 2.0
    trace = Trace(data=data.astype(np.float64))
    trace.stats.network = "XX"
    trace.stats.station = "SIG"
    trace.stats.channel = "BHZ"
    trace.stats.starttime = UTCDateTime("2020-01-01T00:00:00Z")
    trace.stats.sampling_rate = rate

    prepared = trace.copy().detrend("demean").taper(max_percentage=0.02)
    prepared.filter("bandpass", freqmin=1.0, freqmax=20.0,
                    corners=2, zerophase=True)
    assert prepared.stats.npts == n
    assert prepared.stats.processing
    assert np.isfinite(prepared.data).all()

    nsta, nlta = int(0.2 * rate), int(2.0 * rate)
    cft = recursive_sta_lta(prepared.data, nsta, nlta)
    classic = classic_sta_lta(prepared.data, nsta, nlta)
    assert cft.shape == (n,) and classic.shape == (n,)
    onsets = trigger_onset(cft, 2.0, 1.0)
    assert len(onsets) >= 1, "synthetic pulse did not produce a trigger"

    shifted = np.roll(prepared.data, 5)
    correlation = correlate(prepared.data, shifted, shift=20, demean=True,
                            normalize="naive")
    assert np.isfinite(correlation).all()
    assert int(np.argmax(correlation)) >= 0

    Stream([prepared]).verify()
    print("signal smoke checks passed")
    print("trigger_windows:", onsets.tolist())
    print("correlation_peak:", float(np.max(correlation)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
