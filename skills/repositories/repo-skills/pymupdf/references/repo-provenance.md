# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of PyMuPDF. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T19:30:00Z",
  "repository": {
    "name": "PyMuPDF",
    "remote_url": "https://github.com/pymupdf/PyMuPDF.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "53c9aaf539b4fbb6a53010d90de3a2df96e82b5e",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {"name": "pymupdf", "version": "1.28.2", "import_names": ["pymupdf", "fitz"]}
  ],
  "evidence": {
    "source_roots": ["src", "src_classic"],
    "docs": ["README.md", "docs"],
    "examples": ["docs/samples"],
    "tests": ["tests"],
    "configs": ["pyproject.toml", "setup.py", "pytest.ini", "docs/requirements.txt"],
    "scripts": ["scripts", "src/__main__.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the dirty paths differ materially from this snapshot, run `refresh-repo-skill`.
- If package metadata, public entry points, CLI commands, optional dependency boundaries, or documented workflows changed, refresh this skill.
