# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of CellTypist. If the current repo commit, dirty state, package version, public APIs, CLI options, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-29T16:13:34Z",
  "repository": {
    "name": "celltypist",
    "remote_url": "https://github.com/Teichlab/celltypist.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "fe357564a6625d3b1732a022fd39f18e55696e80",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "celltypist",
      "version": "1.7.1",
      "import_names": ["celltypist"]
    }
  ],
  "evidence": {
    "source_roots": ["celltypist"],
    "docs": ["README.md", "docs/source", "docs/notebook"],
    "examples": ["celltypist/data/samples"],
    "tests": [],
    "configs": ["setup.py", "requirements.txt", "MANIFEST.in", "Dockerfile", ".readthedocs.yaml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and the changed relative paths differ from this snapshot, run `refresh-repo-skill` before relying on source-level details.
- If `celltypist.__version__`, `setup.py`, `requirements.txt`, the `celltypist` CLI options, or public signatures for `annotate`, `train`, `dotplot`, `Model`, `Classifier`, or `AnnotationResult` changed, run `refresh-repo-skill`.
- If model cache/download behavior or bundled mapping file names changed, refresh the model-management sub-skill.
