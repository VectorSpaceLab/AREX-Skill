# Repository Provenance

## Purpose

Read this before deciding whether this skill still matches a checkout of the
Once-for-All repository. If the commit, dirty state, package metadata, or major
evidence paths differ from this snapshot, run a refresh workflow instead of
assuming the skill is current.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T18:07:09Z",
  "repository": {
    "name": "once-for-all",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "f03b2673db313b9167e2a1c2b7a5cad540cc1313",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "ofa",
      "version": "0.1.0",
      "import_names": ["ofa"]
    }
  ],
  "evidence": {
    "source_roots": ["ofa"],
    "docs": ["README.md", "tutorial/README.md"],
    "examples": ["tutorial/ofa.ipynb", "tutorial/ofa_resnet50_example.ipynb"],
    "tests": [],
    "scripts": ["eval_ofa_net.py", "eval_specialized_net.py", "hubconf.py", "train_ofa_net.py"],
    "configs": []
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, treat the skill as potentially stale.
- If the working tree becomes dirty relative to this snapshot, re-evaluate the skill.
- If package metadata or public entry points change, refresh the skill even if the commit is unchanged.
