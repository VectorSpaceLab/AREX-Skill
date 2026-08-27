# Repository Provenance

Read this before deciding whether the generated LangExtract guidance is current for a checkout or installed package. If the source commit, package version, public entry points, or major evidence paths differ, refresh the repo skill before relying on version-sensitive claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T16:40:25Z",
  "repository": {
    "name": "langextract",
    "remote_url": "https://github.com/google/langextract.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "b5fe0baf807ac35ec95b968a71e4d03f198a1b60",
    "working_tree": "clean at source snapshot; generated skill and review artifacts are separate outputs",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "langextract",
      "version": "1.6.0",
      "import_names": ["langextract"]
    }
  ],
  "evidence": {
    "source_roots": [
      "langextract/",
      "langextract/core/",
      "langextract/providers/"
    ],
    "docs": [
      "README.md",
      "langextract/providers/README.md",
      "docs/examples/"
    ],
    "examples": [
      "examples/ollama/",
      "examples/custom_provider_plugin/",
      "skills/langextract-usage/"
    ],
    "tests": [
      "tests/init_test.py",
      "tests/extract_schema_integration_test.py",
      "tests/prompt_validation_test.py",
      "tests/resolver_test.py",
      "tests/tokenizer_test.py",
      "tests/io_test.py",
      "tests/visualization_test.py",
      "tests/factory_test.py",
      "tests/provider_plugin_test.py",
      "tests/test_gemini_batch_api.py",
      "tests/openai_batch_test.py"
    ],
    "configs": [
      "pyproject.toml",
      "tox.ini",
      ".pre-commit-config.yaml"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale and run a refresh pass.
- If package metadata changes the distribution version, Python requirement, optional extras, provider entry points, or public API signatures, refresh the affected references and scripts.
- If `langextract/extraction.py`, `factory.py`, `io.py`, `visualization.py`, `core/`, or `providers/` changes materially, re-check the matching sub-skill and native candidates.
- Generated skill output and review artifacts are intentionally not evidence paths for the source package; do not use their presence to infer package freshness.
