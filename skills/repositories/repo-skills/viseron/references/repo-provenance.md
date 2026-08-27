# Repo Provenance

This generated operating skill was created from a Viseron source snapshot and is intended to be refreshed when the repository's component schemas, domain lifecycle, configuration docs, or public behavior change.

## Source snapshot

- Repository: Viseron
- Public remote URL: `https://github.com/roflcoopter/viseron.git`
- Commit: `3908501e2a3d47108c4171898a4dee9493073d5d`
- Branch: `dev`
- Exact tag: none detected at the source commit
- Working tree state at provenance capture: clean
- Python distribution name: `viseron`
- Package version from setup metadata: `0.0.0`

## Evidence paths used

The following paths are relative evidence locations from the source repository snapshot. They are provenance records, not runtime dependencies for this skill.

- `README.md`
- `setup.py`, `pyproject.toml`, `requirements*.txt`, `tox.ini`
- `viseron/`
- `viseron/components/`
- `viseron/domains/`
- `viseron/helpers/`
- `viseron/config.py`, `viseron/reload.py`, `viseron/events.py`, `viseron/states.py`, `viseron/domain_registry.py`
- `docs/docs/documentation/`
- `docs/docs/developers/`
- `docs/src/pages/components-explorer/`
- `scripts/gen_docs/`, `scripts/recreate_db/`
- `tests/`
- `docker/`, `rootfs/`, `azure-pipelines/` as reference-only deployment/build evidence

## Verification baseline

- Construction selected a strict CPU-safe skill scope for static configuration review, source/API inspection, and mocked/unit-test-compatible behavior.
- Optional runtime surfaces that were documented but not locally verified include live cameras, Docker image execution, PostgreSQL service tests, MQTT brokers, notification services, webhooks, external detector services, GStreamer/PyGObject, EdgeTPU, Hailo, CUDA, VA-API, Raspberry Pi, Jetson, model downloads, and credentials.
- The installed-package inspection found that source-root context matters for some subprocess modules because Viseron source includes a top-level `manager.py` helper used by subprocess workers.

## Refresh triggers

Refresh this skill when any of these change materially:

- component explorer generated config JSON or component docs;
- `CONFIG_SCHEMA`, `setup()`, `setup_domains()`, domain dependency, or reload behavior;
- camera/recording/storage tier semantics;
- detector component model/device options or post-processing label behavior;
- MQTT/webhook/notification/PTZ event and template behavior;
- packaging/import requirements, especially the source-root `manager.py` behavior;
- native tests reveal behavior that contradicts this skill's references.
