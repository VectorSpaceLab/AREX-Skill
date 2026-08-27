# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Presidio. If the current repo commit, dirty state, package version, public APIs, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-10T06:34:47Z",
  "repository": {
    "name": "presidio",
    "remote_url": "https://github.com/data-privacy-stack/presidio.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "760d6c83ae89274a268e01aef3e6da7910664a83",
    "working_tree": "clean at source-evidence capture before generated skill files were added",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "presidio",
      "version": "2.2.364",
      "import_names": ["presidio"]
    },
    {
      "name": "presidio_analyzer",
      "version": "2.2.364",
      "import_names": ["presidio_analyzer"]
    },
    {
      "name": "presidio_anonymizer",
      "version": "2.2.364",
      "import_names": ["presidio_anonymizer"]
    },
    {
      "name": "presidio_structured",
      "version": "0.0.8",
      "import_names": ["presidio_structured"]
    },
    {
      "name": "presidio-image-redactor",
      "version": "0.0.60",
      "import_names": ["presidio_image_redactor"]
    },
    {
      "name": "presidio-cli",
      "version": "0.0.9",
      "import_names": ["presidio_cli"]
    }
  ],
  "evidence": {
    "source_roots": [
      "presidio/presidio",
      "presidio-analyzer/presidio_analyzer",
      "presidio-anonymizer/presidio_anonymizer",
      "presidio-structured/presidio_structured",
      "presidio-image-redactor/presidio_image_redactor",
      "presidio-cli/presidio_cli"
    ],
    "docs": [
      "README.MD",
      "docs/installation.md",
      "docs/getting_started.md",
      "docs/getting_started",
      "docs/analyzer",
      "docs/anonymizer",
      "docs/structured",
      "docs/image-redactor",
      "docs/api",
      "docs/supported_entities.md",
      "docs/text_anonymization.md",
      "docs/tutorial"
    ],
    "examples": [
      "docs/samples/python/simple_anonymization_example.py",
      "docs/samples/python/custom_presidio.py",
      "docs/samples/python/example_custom_lambda_anonymizer.py",
      "docs/samples/python/process_csv_file.py",
      "selected docs/samples/python notebooks distilled, not bundled"
    ],
    "tests": [
      "presidio-analyzer/tests",
      "presidio-anonymizer/tests",
      "presidio-structured/tests",
      "presidio-image-redactor/tests",
      "presidio-cli/tests",
      "e2e-tests/tests/test_package_e2e_integration_flows.py"
    ],
    "configs": [
      "presidio-analyzer/presidio_analyzer/conf/default.yaml",
      "presidio-analyzer/presidio_analyzer/conf/default_recognizers.yaml",
      "presidio-cli/presidio_cli/conf/default.yaml",
      "presidio-cli/presidio_cli/conf/limited.yaml",
      "presidio-cli/.presidiocli"
    ],
    "package_metadata": [
      "presidio/pyproject.toml",
      "presidio-analyzer/pyproject.toml",
      "presidio-anonymizer/pyproject.toml",
      "presidio-structured/pyproject.toml",
      "presidio-image-redactor/pyproject.toml",
      "presidio-cli/pyproject.toml"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package versions, public entry points, constructor signatures, CLI flags, supported entities, default model configuration, or optional extras changed, run `refresh-repo-skill`.
- If image OCR or service APIs changed, refresh before relying on image/DICOM or REST guidance.
- If the current checkout has uncommitted changes outside the generated `skills/` output, refresh or verify those changes before using this skill as current evidence.
