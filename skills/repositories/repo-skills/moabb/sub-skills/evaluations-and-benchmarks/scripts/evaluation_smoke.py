#!/usr/bin/env python3
"""Run a tiny, deterministic, offline MOABB evaluation smoke.

The fixture is intentionally not a benchmark: its scores have no scientific
meaning. It checks that a fake two-subject/two-session dataset can pass through
one evaluation, a sklearn pipeline, and the HDF5 result cache without network
access.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path


def _run_once() -> dict:
    from mne.decoding import Vectorizer
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.pipeline import make_pipeline

    from moabb.datasets.fake import FakeDataset
    from moabb.evaluations import WithinSessionEvaluation
    from moabb.paradigms import FakeImageryParadigm

    dataset = FakeDataset(
        event_list=("left_hand", "right_hand"),
        n_sessions=2,
        n_runs=1,
        n_subjects=2,
        code="FakeDataset",
        paradigm="imagery",
        channels=("C3", "Cz", "C4"),
        seed=7,
        sfreq=128,
        duration=4,
        n_events=12,
    )
    pipeline = make_pipeline(Vectorizer(), LinearDiscriminantAnalysis())

    with tempfile.TemporaryDirectory(prefix="moabb-eval-smoke-") as temp_dir:
        evaluation = WithinSessionEvaluation(
            paradigm=FakeImageryParadigm(),
            datasets=[dataset],
            random_state=13,
            n_jobs=1,
            overwrite=True,
            suffix="tiny",
            hdf5_path=Path(temp_dir),
        )
        results = evaluation.process({"vectorizer_lda": pipeline})
        if results.empty:
            raise AssertionError("the fake evaluation returned no result rows")

        subjects = set(results["subject"].astype(str))
        sessions = set(results["session"].astype(str))
        if subjects != {"1", "2"}:
            raise AssertionError(f"expected two subjects, observed {sorted(subjects)}")
        if sessions != {"0", "1"}:
            raise AssertionError(f"expected two sessions, observed {sorted(sessions)}")
        if "score" not in results or results["score"].isna().any():
            raise AssertionError("result rows do not contain finite primary scores")

        return {
            "rows": int(len(results)),
            "subjects": sorted(subjects),
            "sessions": sorted(sessions),
            "scores": [float(value) for value in results["score"]],
            "result_columns": sorted(str(column) for column in results.columns),
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a tiny offline deterministic MOABB FakeDataset evaluation."
    )
    parser.add_argument(
        "--tiny-fixture",
        action="store_true",
        help="run the smoke (the flag makes intent explicit; it is otherwise the default)",
    )
    args = parser.parse_args()
    del args

    first = _run_once()
    second = _run_once()
    if first["scores"] != second["scores"]:
        raise AssertionError("repeated fake evaluations produced different scores")

    print(json.dumps({"status": "ok", "deterministic": True, **first}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
