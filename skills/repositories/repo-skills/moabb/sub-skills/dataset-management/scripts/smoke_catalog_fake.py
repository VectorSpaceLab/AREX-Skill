#!/usr/bin/env python3
"""Run a tiny offline MOABB catalog/FakeDataset smoke check.

This helper only instantiates catalog objects and synthetic MNE data. It never
calls ``data_path``, ``download``, or a real dataset's ``get_data``.
"""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke-test MOABB catalog search and FakeDataset offline."
    )
    parser.add_argument(
        "--catalog",
        action="store_true",
        help="Also instantiate imagery catalog candidates (no subject data).",
    )
    parser.add_argument("--subjects", type=int, default=2, help="Fake subjects (default: 2).")
    parser.add_argument("--sessions", type=int, default=2, help="Fake sessions (default: 2).")
    args = parser.parse_args()
    if args.subjects < 1 or args.sessions < 1:
        parser.error("--subjects and --sessions must be positive")

    from moabb.datasets import FakeDataset

    dataset = FakeDataset(
        event_list=("left", "right"),
        n_subjects=args.subjects,
        n_sessions=args.sessions,
        n_runs=1,
        channels=("C3", "C4"),
        sfreq=32,
        duration=4,
        n_events=4,
        seed=17,
        annotations=True,
        subjects=list(range(1, args.subjects + 1)),
        sessions=list(range(args.sessions)),
    )
    data = dataset.get_data()
    if set(data) != set(range(1, args.subjects + 1)):
        raise RuntimeError("fake subject selection did not round-trip")
    if any(len(subject_data) != args.sessions for subject_data in data.values()):
        raise RuntimeError("fake session selection did not round-trip")
    first = data[1]["0"]["0"]
    if first.info["sfreq"] != 32 or set(first.ch_names) != {"C3", "C4", "stim"}:
        raise RuntimeError("unexpected FakeDataset raw structure")
    print(f"fake_subjects={len(data)} fake_sessions={len(data[1])}")
    print(f"fake_channels={first.ch_names} sfreq={first.info['sfreq']}")
    print("network=not attempted")

    if args.catalog:
        from moabb.datasets.utils import dataset_search

        candidates = dataset_search(paradigm="imagery", multi_session=True, min_subjects=2)
        print(f"imagery_multi_session_candidates={len(candidates)}")
        print("catalog_data_loading=not requested")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
