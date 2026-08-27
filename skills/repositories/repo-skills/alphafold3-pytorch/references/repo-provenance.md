# Repository Provenance

Read this before deciding whether the operating skill is current for a
checkout. If the source commit, package version, public entry points, or major
evidence paths differ, use `refresh-repo-skill` before relying on detailed
claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T00:00:00Z",
  "repository": {
    "name": "alphafold3-pytorch",
    "remote_url": "https://github.com/lucidrains/alphafold3-pytorch",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a52ca288977ed1fc1565dded0a8b434d3dc5201d",
    "working_tree": "clean-at-source-snapshot",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "alphafold3-pytorch",
      "version": "0.8.3",
      "import_names": ["alphafold3_pytorch"]
    }
  ],
  "evidence": {
    "source_roots": ["alphafold3_pytorch"],
    "docs": ["README.md", "docs/alphafold3-supplementary.pdf", "pyproject.toml", "Dockerfile"],
    "examples": ["README.md"],
    "tests": ["tests", "tests/configs"],
    "configs": ["tests/configs", "pyproject.toml"],
    "scripts": ["scripts"],
    "fixtures": ["data/test"]
  }
}
```

The source snapshot was clean before this generated skill and its review
artifacts were added under the repository's `skills/` area. Those generated
outputs are not source evidence and should not be treated as package changes.

## Refresh check

- Compare `git rev-parse HEAD` with the recorded commit.
- Compare package metadata and console entry points with the snapshot.
- If source, docs, tests, configs, or public APIs changed, refresh rather than
  patching a stale route from memory.
- Recheck the CCD/MSA/template data assumptions and PyTorch backend claims when
  refreshing; they are version- and environment-sensitive.
