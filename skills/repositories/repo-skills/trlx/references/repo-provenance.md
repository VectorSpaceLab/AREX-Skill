# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of trlX. If the current repo commit, package metadata, public APIs, or evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T19:39:20Z",
  "repository": {
    "name": "trlx",
    "remote_url": "https://github.com/CarperAI/trlx.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "3340c2f3a56d1d14fdd5f13ad575121fa26b6d92",
    "working_tree": "clean",
    "dirty_paths": [],
    "snapshot_note": "Source snapshot was captured before generated skill artifacts were added under skills/. Generated skill/test artifacts are not part of the source baseline."
  },
  "packages": [
    {
      "name": "trlx",
      "version": "0.7.0",
      "import_names": ["trlx"]
    }
  ],
  "evidence": {
    "source_roots": ["trlx"],
    "docs": ["README.md", "docs/source", "trlx/models/README.md"],
    "examples": ["examples"],
    "tests": ["tests"],
    "configs": ["configs"],
    "scripts": ["scripts"],
    "package_metadata": ["pyproject.toml", "setup.cfg", "setup.py", "requirements.txt", "docs/requirements.txt"],
    "existing_skill_evidence": ["skills/trlx.log"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale.
- If package metadata, trainer/config registries, public examples, or default config helpers changed, refresh even if the commit looks similar.
- If the current checkout has unrelated source changes outside generated skill artifacts, refresh or re-verify the affected workflows.
- If only generated `skills/` artifacts differ, that alone does not mean the source package behavior changed.
