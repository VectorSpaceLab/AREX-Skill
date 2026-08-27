# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T11:12:51Z",
  "repository": {
    "name": "detrex",
    "remote_url": "https://github.com/IDEA-Research/detrex.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e244e6c3da3e84566728c52c21fb061d23ce0e2f",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "detrex",
      "version": "0.3.0",
      "import_names": ["detrex"]
    }
  ],
  "evidence": {
    "source_roots": ["detrex/"],
    "docs": ["README.md", "docs/source/tutorials/", "docs/source/modules/", "projects/*/README.md", "tools/README.md", "demo/README.md"],
    "examples": ["demo/", "tools/", "projects/*/configs/", "projects/*/converter.py", "projects/*/train_net.py"],
    "tests": ["tests/"],
    "configs": ["configs/common/", "configs/hydra/train_args.yaml", "projects/*/configs/"]
  }
}
```

The snapshot records the source state used to distill this skill. Generated skill files themselves are not source evidence and are excluded from the dirty-state baseline.

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public imports, config fragments, trainer/tool scripts, or project READMEs changed, run `refresh-repo-skill` even when the commit is the same.
- If a task depends on a new model family, new dataset mapper, or changed Detectron2/PyTorch compatibility, refresh before relying on old guidance.
