# Repository Provenance

## Purpose

Read this before deciding whether the ICEdit skill matches a checkout of the repository. If the current commit, dirty state, or evidence paths differ materially from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-19T13:09:27Z",
  "repository": {
    "name": "ICEdit",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "74a8f830292b420e96255189a68a183e6b10bcfe",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "diffusers",
      "version": "0.33.0",
      "import_names": ["diffusers"]
    },
    {
      "name": "torch",
      "version": "2.7.0+cu126",
      "import_names": ["torch"]
    },
    {
      "name": "transformers",
      "version": "4.51.3",
      "import_names": ["transformers"]
    },
    {
      "name": "gradio",
      "version": "6.17.3",
      "import_names": ["gradio"]
    },
    {
      "name": "lightning",
      "version": "2.6.5",
      "import_names": ["lightning"]
    }
  ],
  "evidence": {
    "source_roots": ["scripts", "train/src", "icedit"],
    "docs": ["README.md", "train/README.md"],
    "examples": ["assets", "train/assets"],
    "configs": ["requirements.txt", "train/requirements.txt", "sub-skills/gradio/scripts/config.json", "train/train/config"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, the skill may be stale.
- If the repository becomes clean or the dirty paths change materially, regenerate provenance and review the skill.
- If the shipped dependency surface changes enough to affect the helper scripts or training launch assumptions, refresh the skill even if the commit is unchanged.
