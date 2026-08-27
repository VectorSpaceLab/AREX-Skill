# Repository Provenance

Read this before deciding whether this skill is current for a checkout. Refresh if commit, package versions, public APIs, entry points, or major evidence paths differ.

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T00:00:00Z",
  "repository": {
    "name": "PySyft",
    "remote_url": "https://github.com/OpenMined/PySyft.git",
    "vcs": "git",
    "branch": "dev",
    "tag": null,
    "commit": "91fd3b146ebb9523bbd1a914d1cc7bb5327ff0c7",
    "working_tree": "dirty-generated-skill-and-build-artifacts",
    "dirty_paths": ["skills/", "syft_client.egg-info", "__pycache__"]
  },
  "packages": [
    {"name": "syft-client", "version": "0.1.117", "import_names": ["syft_client"]},
    {"name": "syft-rds", "version": "0.1.0", "import_names": ["syft_rds"]},
    {"name": "syft-dataset", "version": "0.1.20", "import_names": ["syft_datasets"]},
    {"name": "syft-job", "version": "0.1.39", "import_names": ["syft_job"]},
    {"name": "syft-bg", "version": "0.3.11", "import_names": ["syft_bg"]},
    {"name": "syft-enclave", "version": "0.1.0", "import_names": ["syft_enclaves"]},
    {"name": "syft-restrict", "version": "0.1.0", "import_names": ["syft_restrict"]},
    {"name": "syft-permissions", "version": "0.1.14", "import_names": ["syft_permissions"]},
    {"name": "syft-perms", "version": "0.1.14", "import_names": ["syft_perms"]},
    {"name": "syft-migration", "version": "0.1.0", "import_names": ["syft_migration"]},
    {"name": "syft-notebook-ui", "version": "0.1.1", "import_names": ["syft_notebook_ui"]}
  ],
  "evidence": {
    "source_roots": ["syft_client/", "packages/*/src/"],
    "docs": ["README.md", "docs/", "packages/*/README.md", "packages/*/docs/"],
    "tests": ["tests/unit/", "packages/*/tests/"],
    "examples": ["packages/syft-restrict/examples/", "packages/enclave-model-api-example/", "notebooks/"]
  }
}
```

Real Google Drive, Gmail, GCP, TEE, and GPU behavior was intentionally not live-verified because credentials and cloud hardware were not provided.
