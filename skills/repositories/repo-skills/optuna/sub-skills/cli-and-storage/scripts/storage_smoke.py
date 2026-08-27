#!/usr/bin/env python3
"""Smoke-test local Optuna RDBStorage and JournalStorage workflows."""

from __future__ import annotations

import tempfile
from pathlib import Path

import optuna
from optuna.storages import JournalStorage
from optuna.storages import RDBStorage
from optuna.storages.journal import JournalFileBackend


def objective(trial: optuna.Trial) -> float:
    x = trial.suggest_float("x", -1.0, 1.0)
    return (x - 0.25) ** 2


def check_rdb_storage(temp_dir: Path) -> None:
    db_path = temp_dir / "rdb.db"
    storage_url = f"sqlite:///{db_path}"
    storage = RDBStorage(storage_url)
    study = optuna.create_study(
        study_name="rdb-smoke",
        storage=storage,
        direction="minimize",
        load_if_exists=True,
    )
    study.optimize(objective, n_trials=2)

    resumed = optuna.load_study(study_name="rdb-smoke", storage=storage_url)
    if len(resumed.trials) != 2:
        raise AssertionError(f"expected 2 RDB trials, got {len(resumed.trials)}")
    if resumed.best_value is None:
        raise AssertionError("RDB study did not produce a best value")


def check_journal_storage(temp_dir: Path) -> None:
    journal_path = temp_dir / "journal.log"
    storage = JournalStorage(JournalFileBackend(str(journal_path)))
    study = optuna.create_study(
        study_name="journal-smoke",
        storage=storage,
        direction="minimize",
        load_if_exists=True,
    )
    study.optimize(objective, n_trials=2)

    resumed_storage = JournalStorage(JournalFileBackend(str(journal_path)))
    resumed = optuna.load_study(study_name="journal-smoke", storage=resumed_storage)
    if len(resumed.trials) != 2:
        raise AssertionError(f"expected 2 journal trials, got {len(resumed.trials)}")
    if not journal_path.exists() or journal_path.stat().st_size == 0:
        raise AssertionError("journal log was not created")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="optuna-storage-smoke-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        check_rdb_storage(temp_dir)
        check_journal_storage(temp_dir)
    print("Optuna local storage smoke succeeded")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
