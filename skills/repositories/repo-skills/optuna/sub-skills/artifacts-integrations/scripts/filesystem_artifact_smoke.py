#!/usr/bin/env python
from __future__ import annotations

from pathlib import Path
import tempfile

import optuna
from optuna.artifacts import FileSystemArtifactStore
from optuna.artifacts import download_artifact
from optuna.artifacts import get_all_artifact_meta
from optuna.artifacts import upload_artifact


EXPECTED_PREFIX = "trial-report:"
STUDY_MANIFEST = "study-manifest:artifact-smoke"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="optuna-artifact-smoke-") as tmpdir:
        root = Path(tmpdir)
        artifact_dir = root / "artifacts"
        artifact_dir.mkdir()
        artifact_store = FileSystemArtifactStore(artifact_dir)

        study = optuna.create_study(direction="minimize")

        def objective(trial: optuna.Trial) -> float:
            x = trial.suggest_float("x", -1.0, 1.0)
            report_text = f"{EXPECTED_PREFIX}{trial.number}:x={x:.6f}\n"
            report_path = root / f"trial-{trial.number}-report.txt"
            report_path.write_text(report_text, encoding="utf-8")
            artifact_id = upload_artifact(
                artifact_store=artifact_store,
                file_path=str(report_path),
                study_or_trial=trial,
                mimetype="text/plain",
            )
            trial.set_user_attr("report_artifact_id", artifact_id)
            trial.set_user_attr("report_text", report_text)
            return x * x

        study.optimize(objective, n_trials=1)

        manifest_path = root / "study-manifest.txt"
        manifest_path.write_text(STUDY_MANIFEST + "\n", encoding="utf-8")
        study_artifact_id = upload_artifact(
            artifact_store=artifact_store,
            file_path=str(manifest_path),
            study_or_trial=study,
            mimetype="text/plain",
        )

        best_trial = study.best_trial
        trial_artifact_id = best_trial.user_attrs["report_artifact_id"]
        trial_metas = get_all_artifact_meta(best_trial, storage=study._storage)
        study_metas = get_all_artifact_meta(study)

        assert len(trial_metas) == 1, trial_metas
        assert trial_metas[0].artifact_id == trial_artifact_id
        assert trial_metas[0].filename.endswith("report.txt")
        assert trial_metas[0].mimetype == "text/plain"
        assert len(study_metas) == 1, study_metas
        assert study_metas[0].artifact_id == study_artifact_id

        downloaded = root / "downloaded-report.txt"
        download_artifact(
            artifact_store=artifact_store,
            artifact_id=trial_artifact_id,
            file_path=str(downloaded),
        )
        downloaded_text = downloaded.read_text(encoding="utf-8")
        assert downloaded_text == best_trial.user_attrs["report_text"]
        assert downloaded_text.startswith(EXPECTED_PREFIX)

        print("ok: filesystem artifact upload/list/download roundtrip")
        print(f"trial_artifact_id={trial_artifact_id}")
        print(f"study_artifact_id={study_artifact_id}")


if __name__ == "__main__":
    main()
