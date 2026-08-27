# Repository Provenance

Read this before using the skill with another MedRAX checkout. If the commit,
working-tree state, package metadata, or major evidence paths differ, run a
refresh rather than assuming the operating graph is current.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T18:03:36Z",
  "repository": {
    "name": "MedRAX",
    "remote_url": "https://github.com/bowang-lab/MedRAX",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "dae30e2f136ef0b2a40885a4c335386e9ffad052",
    "working_tree": "dirty-untracked",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "medrax",
      "version": "0.1.0",
      "import_names": ["medrax"]
    }
  ],
  "evidence": {
    "source_roots": ["medrax", "main.py", "interface.py"],
    "docs": ["README.md", "medrax/docs/system_prompts.txt"],
    "examples": ["quickstart.py", "demo/chest"],
    "tests": [],
    "configs": ["pyproject.toml"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `dae30e2f136ef0b2a40885a4c335386e9ffad052`, treat this skill as potentially stale.
- If the checkout's dirty/untracked state changes materially, especially
  `pyproject.toml`, `README.md`, `main.py`, `interface.py`, `medrax/`, or
  `quickstart.py`, refresh the skill.
- Recheck the declared Transformers Git revision, Torch/Gradio/LangGraph
  compatibility, public tool names/schemas, and model-resource requirements
  before updating claims.
- No repository test suite was present in the captured checkout. Utility and
  schema checks are therefore more important than a nonexistent native test
  command; weight-backed inference remains separately gated by model assets,
  backend, and credentials.
