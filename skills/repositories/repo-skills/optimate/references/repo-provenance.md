# Repository Provenance

## Purpose

Read this before deciding whether the skill is current for a checkout of the repository.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T17:16:00Z",
  "repository": {
    "name": "optimate",
    "remote_url": "https://github.com/nebuly-ai/optimate.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a6d302f912b481c94370811af6b11402f51d377f",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {"name": "speedster", "version": "0.4.0", "import_names": ["speedster"]},
    {"name": "nebullvm", "version": "0.10.0", "import_names": ["nebullvm"]},
    {"name": "forward_forward", "version": "0.0.1", "import_names": ["forward_forward"]},
    {"name": "OpenAlphaTensor", "version": "0.0.1", "import_names": ["open_alpha_tensor"]},
    {"name": "chatllama-py", "version": "0.0.4", "import_names": ["chatllama"]}
  ],
  "evidence": {
    "source_roots": [
      "optimization/speedster/speedster",
      "optimization/nebullvm/nebullvm",
      "optimization/forward_forward/forward_forward",
      "optimization/open_alpha_tensor/open_alpha_tensor",
      "optimization/chatllama/chatllama"
    ],
    "docs": [
      "README.md",
      "optimization/speedster/README.md",
      "optimization/speedster/docs/en/docs",
      "optimization/nebullvm/README.md",
      "optimization/forward_forward/README.md",
      "optimization/open_alpha_tensor/README.md",
      "optimization/chatllama/README.md"
    ],
    "examples": [
      "optimization/speedster/notebooks",
      "optimization/chatllama/artifacts",
      "optimization/open_alpha_tensor/main.py"
    ],
    "tests": [
      "optimization/speedster/speedster/tests",
      "optimization/speedster/speedster/api/tests",
      "optimization/nebullvm/nebullvm/**/tests"
    ],
    "configs": [
      "optimization/chatllama/artifacts/config/config.yaml",
      "optimization/chatllama/artifacts/config/ds_config.json",
      "optimization/chatllama/artifacts/config/peft_config.yaml",
      "optimization/open_alpha_tensor/config.json"
    ]
  }
}
```

## Refresh check

If the commit, dirty state, package versions, public import roots, or package entry points change, refresh the skill. Keep the provenance file public and relative-path only.
