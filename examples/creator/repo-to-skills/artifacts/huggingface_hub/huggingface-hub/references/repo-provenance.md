# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
`huggingface/huggingface_hub`. If the source commit, package version, public
entry points, or major evidence paths differ, use a refresh workflow before
relying on detailed behavior.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-31T11:13:43Z",
  "repository": {
    "name": "huggingface_hub",
    "remote_url": "https://github.com/huggingface/huggingface_hub.git",
    "vcs": "git",
    "branch": "v1.29.0",
    "tag": "v1.29.0",
    "commit": "4237d95c603db491cb1070898c74c97e4d7c2582",
    "working_tree": "clean at source snapshot; generated skill/artifacts are output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "huggingface_hub",
      "version": "1.29.0",
      "import_names": ["huggingface_hub"]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/huggingface_hub",
      "src/huggingface_hub/cli",
      "src/huggingface_hub/inference",
      "src/huggingface_hub/serialization"
    ],
    "docs": [
      "README.md",
      "docs/source/en",
      "docs/source/en/guides",
      "docs/source/en/package_reference"
    ],
    "examples": [],
    "tests": [
      "tests/test_hf_api.py",
      "tests/test_cli.py",
      "tests/test_file_download.py",
      "tests/test_inference_client.py",
      "tests/test_serialization.py",
      "tests/test_dduf.py",
      "tests/test_jobs_api.py",
      "tests/test_sandbox.py",
      "tests/test_repocard.py",
      "tests/test_webhooks_server.py",
      "tests/test_utils_hf_uris.py",
      "tests/test_utils_cache.py"
    ],
    "configs": [
      "setup.py",
      "pyproject.toml",
      "Makefile",
      "AGENTS.md",
      "CONTRIBUTING.md"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
potentially stale and refresh it.
- If the source working tree was not clean at the recorded snapshot, compare
recorded relative dirty paths before trusting behavior. The generated skill and
its review artifacts are output and are not source evidence.
- If package metadata, CLI entry points, inference providers, generated public
exports, or the major source/doc paths change, refresh even when the commit is
unchanged in a reconstructed checkout.
- The snapshot was taken from the public `huggingface/huggingface_hub`
repository at the `v1.29.0` tag. The authoritative source license resolved for
this commit is `Apache-2.0`.
