---
name: artifacts-integrations
description: "Use this sub-skill for Optuna artifact upload/download workflows,
  filesystem/S3/GCS artifact stores, optional integration callback imports,
  cloud credential boundaries, and local artifact roundtrip checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Optuna Artifacts and Integrations

Use this sub-skill when the task involves storing files produced by Optuna studies or wiring Optuna to third-party ML/framework services through `optuna.artifacts` or `optuna.integration`.

## Route Here For

- Uploading or downloading artifacts with `optuna.artifacts.upload_artifact`, `download_artifact`, and `get_all_artifact_meta`.
- Choosing or configuring `FileSystemArtifactStore`, `Boto3ArtifactStore`, or `GCSArtifactStore`.
- Attaching model checkpoints, reports, images, generated data, or study-level metadata files to a trial or study.
- Handling optional integration imports such as `LightGBMPruningCallback`, `XGBoostPruningCallback`, `MLflowCallback`, `OptunaSearchCV`, and `WeightsAndBiasesCallback`.
- Detecting missing optional packages, missing cloud SDKs, missing credentials, or unsafe remote-service assumptions and selecting a local fallback.

## Route Elsewhere

- Objective authoring, `Study.optimize`, `Study.ask`, `Study.tell`, callbacks unrelated to third-party frameworks, and trial state transitions: use `../optimization-workflows/SKILL.md`.
- Persistent study storage, `RDBStorage`, `JournalStorage`, CLI commands, schema upgrades, and heartbeat behavior: use `../cli-and-storage/SKILL.md`.
- Sampler/pruner algorithms and search-space design: use `../samplers-pruners/SKILL.md`.
- Plotting, parameter importances, dashboards, and visual result analysis: use `../analysis-visualization/SKILL.md`.

## Primary References

- Artifact API patterns, store selection, metadata handling, and filesystem/S3/GCS boundaries: `references/artifact-workflows.md`.
- Integration import routing, optional dependency probes, and callback selection: `references/integration-reference.md`.
- Source-backed failures and fixes for artifact and integration tasks: `references/troubleshooting.md`.

## Bundled Smoke Script

Run the deterministic local artifact roundtrip check with an environment where `optuna` is importable. From this sub-skill directory, use:

```bash
python scripts/filesystem_artifact_smoke.py
```

The script creates a temporary `FileSystemArtifactStore`, optimizes a tiny in-memory study, uploads one trial artifact and one study artifact, lists metadata, downloads the trial artifact, verifies byte-for-byte content, and exits without external services.

## Operational Defaults

- Prefer `FileSystemArtifactStore(base_path=...)` for local, CI, tutorials, and smoke checks because it needs no optional dependency or credentials.
- Keep artifact stores separate from Optuna study storage: study/trial metadata lives in Optuna storage, while file bytes live in the artifact store.
- Use keyword arguments for `upload_artifact(*, artifact_store, file_path, study_or_trial, storage=None, mimetype=None, encoding=None)` and `download_artifact(*, artifact_store, file_path, artifact_id)`.
- Store artifact IDs or use `get_all_artifact_meta(study_or_trial, storage=...)`; Optuna does not infer which artifact store was used later, so the caller must persist or reconstruct that configuration.
- For S3/GCS, verify SDK installation and credentials before constructing stores; do not make network calls in smoke tests unless the user explicitly provides credentials and permits remote access.
