# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of WhisperX. If the current repository commit, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T17:48:18Z",
  "repository": {
    "name": "whisperX",
    "remote_url": "https://github.com/m-bain/whisperX.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "2cfd7b7c5c7bba144954364db747319b50e8232b",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "whisperx",
      "version": "3.8.7rc1",
      "import_names": ["whisperx"]
    }
  ],
  "evidence": {
    "source_roots": ["whisperx/", "whisperx/vads/"],
    "docs": ["README.md", "EXAMPLES.md", "CUDNN_TROUBLESHOOTING.md"],
    "examples": ["README.md CLI/Python examples", "EXAMPLES.md multilingual examples"],
    "tests": ["tests/test_word_timestamp_interpolation.py"],
    "configs": ["pyproject.toml", ".python-version", "MANIFEST.in", ".github/workflows/tests.yml", ".github/workflows/python-compatibility.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public top-level API wrappers, the `whisperx` CLI entry point, or major source modules changed, run `refresh-repo-skill` even if the commit is similar.
- If a checkout contains untracked generated skill artifacts under `skills/`, do not treat those artifacts alone as source-code drift; compare the actual package source, docs, tests, and metadata paths listed above.
