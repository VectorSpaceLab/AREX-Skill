# Repository provenance

Read this before deciding whether the skill matches a source checkout. If the
commit, package metadata, dirty state, or evidence paths differ materially, use
`refresh-repo-skill` rather than silently trusting this graph.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T07:30:00Z",
  "repository": {
    "name": "DeepDanbooru",
    "remote_url": "https://github.com/KichangKim/DeepDanbooru",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "7971936c0d050c6475b01e0eb97710a66c61b43e",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "deepdanbooru",
      "version": "1.0.0",
      "import_names": ["deepdanbooru"]
    }
  ],
  "evidence": {
    "source_roots": ["deepdanbooru/", "deepdanbooru/commands/", "deepdanbooru/data/", "deepdanbooru/model/", "deepdanbooru/project/"],
    "docs": ["README.md", "setup.py", "setup.cfg", "requirements.txt"],
    "examples": [],
    "tests": ["tests/test_main.py"],
    "configs": ["project.json defaults in deepdanbooru/project/project.py"]
  }
}
```

## Refresh checks

- Compare `git rev-parse HEAD` with the snapshot commit.
- Compare public command registration in `deepdanbooru/__main__.py`.
- Compare `README.md`, `requirements.txt`, `setup.py`, project defaults, and
  model/loss dispatch values.
- Recheck the documented `evaluate-project` loader defect before removing the
  fallback guidance.
- The dirty `skills/` path is the generated artifact area; it is not source
  evidence for package behavior.
