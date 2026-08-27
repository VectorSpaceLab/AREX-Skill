# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the DARTS repository. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:37:52Z",
  "repository": {
    "name": "darts",
    "remote_url": "https://github.com/quark0/darts.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "f276dd346a09ae3160f8e3aca5c7b193fda1da37",
    "working_tree": "clean at source-evidence capture; generated skill outputs were written afterward under skills/",
    "dirty_paths": []
  },
  "packages": [],
  "package_note": "No installable Python distribution metadata was present; this is a script-style research repository. README runtime target is Python >=3.5.5, PyTorch ==0.3.1, torchvision ==0.2.0.",
  "evidence": {
    "source_roots": ["cnn", "rnn"],
    "docs": ["README.md"],
    "examples": [],
    "tests": [],
    "configs": [],
    "data_placeholders": ["data/penn/.keep", "data/wikitext-2/.keep", "data/imagenet/.keep"],
    "figures": ["img"]
  },
  "generated_skill": {
    "root": "skills/disco/quark0-darts",
    "imported": false
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, README workflow commands, or the `cnn/` and `rnn/` script surfaces change, refresh this skill.
- If the repository gains a modern package definition, update the runtime guidance and package-inspection assumptions.
- Ignore generated `skills/` output itself when deciding whether source evidence changed, unless the task is specifically about this generated skill.
