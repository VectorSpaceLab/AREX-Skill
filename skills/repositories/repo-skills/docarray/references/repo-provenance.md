# Repository Provenance

## Purpose

Read this before deciding whether the generated skill is current for a DocArray checkout. If the commit, dirty state, package metadata, or public evidence paths differ materially, run a refresh/review cycle before relying on the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-19T06:30:54Z",
  "repository": {
    "name": "docarray",
    "remote_url": "https://github.com/docarray/docarray.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "f5fc0f6d5f3dcb0201dc735262ef3256bdf054b9",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "docarray",
      "version": "0.41.0",
      "import_names": ["docarray"],
      "source_version_constant_observed": "0.40.2",
      "version_status": "snapshot-version-drift-warning"
    }
  ],
  "evidence": {
    "source_roots": ["docarray/"],
    "docs": ["README.md", "docs/user_guide/representing", "docs/user_guide/sending", "docs/user_guide/storing", "docs/how_to/multimodal_training_and_serving.md"],
    "examples": ["README.md", "docs/user_guide/"],
    "tests": ["tests/integrations/document", "tests/units/array", "tests/integrations/store", "tests/index/in_memory", "tests/index/base_classes"],
    "configs": ["pyproject.toml", "mkdocs.yml", "pytest configuration in pyproject.toml"]
  }
}
```

## Snapshot/version drift warning

The two version strings above are independent observations from this snapshot: package metadata reported `0.41.0`, while the checked-in source constant reported `0.40.2`. This is a snapshot/version drift warning, not a claim that either string is the authoritative release version and not evidence that another checkout or installed wheel has the same API surface. Do not normalize, choose between, or publish either value as the snapshot's definitive version without a refreshed inspection.

When refreshing this provenance record, read the package metadata and the source version constant from the same checkout, record both observed values, and retain this warning whenever they differ. Replace the values only with newly observed values from that refresh. Remove the warning only after inspecting the same checkout and the relevant built/installed distribution and confirming that the values are reconciled.

## Refresh checks

- If `git rev-parse HEAD` differs from the recorded commit, review the public API and rerun verification.
- If the checkout becomes clean or the generated `skills/` paths change, update the provenance baseline before publication.
- If `pyproject.toml` changes optional extras, Python support, package entry points, or backend client constraints, review the installation and optional-backend references.
- If package metadata or the source version constant changes, re-observe both from the same checkout. Keep the snapshot/version drift warning while they differ; remove it only under the reconciliation rule above.
