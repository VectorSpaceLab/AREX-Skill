# Repository Provenance

## Purpose

Read this before deciding whether this skill is still aligned with the current OFA checkout. If the current commit, dirty state, package versions, or major evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T23:56:45Z",
  "repository": {
    "name": "OFA",
    "remote_url": "https://github.com/OFA-Sys/OFA.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a36b91ce86ff105ac8d9e513aa88f42b85e33479",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "fairseq",
      "version": "1.0.0a0+a36b91c",
      "import_names": ["fairseq"]
    },
    {
      "name": "torch",
      "version": "2.3.1",
      "import_names": ["torch"]
    },
    {
      "name": "torchvision",
      "version": "0.18.1",
      "import_names": ["torchvision"]
    },
    {
      "name": "torchaudio",
      "version": "2.3.1",
      "import_names": ["torchaudio"]
    }
  ],
  "evidence": {
    "source_roots": [
      "fairseq/",
      "models/",
      "tasks/",
      "data/",
      "criterions/",
      "utils/"
    ],
    "docs": [
      "README.md",
      "README_mmspeech.md",
      "README_EncouragingLoss.md",
      "datasets.md",
      "checkpoints.md",
      "checkpoints_cn.md",
      "prompt_tuning.md",
      "transformers.md",
      "modelscope.md",
      "spaces.md",
      "colab.md"
    ],
    "examples": [
      "run_scripts/"
    ],
    "tests": []
    "configs": [
      "requirements.txt",
      "fairseq/pyproject.toml",
      "fairseq/setup.py",
      "fairseq/fairseq/version.txt"
    ]
  }
}
```

## Refresh Check

- If the current `git rev-parse HEAD` differs from the snapshot commit, treat the skill as potentially stale and refresh it.
- If the dirty-path set changes materially, refresh it.
- If the repo's CLI flags, task registrations, or workflow docs change, refresh it even if the commit is unchanged.
