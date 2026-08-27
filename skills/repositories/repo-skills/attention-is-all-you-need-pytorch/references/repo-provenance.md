# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package metadata, public
entry points, or major evidence paths differ from this snapshot, run
`refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T18:14:08Z",
  "repository": {
    "name": "attention-is-all-you-need-pytorch",
    "remote_url": "https://github.com/jadore801120/attention-is-all-you-need-pytorch.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "132907dd272e2cc92e3c10e6c4e783a87ff8893d",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["transformer"]
    }
  ],
  "evidence": {
    "source_roots": ["transformer"],
    "docs": ["README.md"],
    "examples": ["train_multi30k_de_en.sh"],
    "scripts": ["preprocess.py", "train.py", "translate.py", "apply_bpe.py", "learn_bpe.py", "train_multi30k_de_en.sh"],
    "tests": [],
    "configs": ["requirements.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or this
  snapshot was dirty and the dirty paths differ, run `refresh-repo-skill`.
- If `train.py`, `translate.py`, `preprocess.py`, `transformer/`, or dependency
  expectations change even at the same commit, run `refresh-repo-skill`.
- If the repository gains packaging metadata, console entry points, new tests,
  or a completed BPE translation workflow, refresh the skill before relying on
  old routing or caveats.
