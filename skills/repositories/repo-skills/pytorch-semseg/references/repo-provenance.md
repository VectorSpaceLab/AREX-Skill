# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T19:17:37Z",
  "repository": {
    "name": "pytorch-semseg",
    "remote_url": "https://github.com/meetps/pytorch-semseg.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "801fb200547caa5b0d91b8dde56b837da029f746",
    "working_tree": "clean-source-baseline-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "pytorch-semseg",
      "version": null,
      "import_names": ["ptsemseg"],
      "notes": "README advertises a PyPI release, but this checkout contains no setup.py or pyproject.toml package metadata."
    }
  ],
  "evidence": {
    "source_roots": ["ptsemseg"],
    "docs": ["README.md"],
    "examples": [],
    "tests": [],
    "configs": ["configs/fcn8s_pascal.yml", "configs/frrnB_cityscapes.yml"],
    "scripts": ["train.py", "validate.py", "test.py"],
    "metadata": ["requirements.txt", "LICENSE"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, supported model ids, loader keys, config schema, or top-level entry point flags change, run `refresh-repo-skill`.
- If a future checkout adds packaging metadata, console entry points, tests, examples, or docs that are absent from this snapshot, refresh the skill so routing and bundled helpers can use that evidence.
- If local generated skill artifacts make a source checkout dirty, distinguish those generated files from source changes before deciding staleness.
