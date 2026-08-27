# Repository Provenance

## Purpose

Read this before deciding whether the Qwen operating graph is current for a checkout. If the source commit, dirty state, public entry points, dependency guidance, or major evidence paths differ, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T06:59:24Z",
  "repository": {
    "name": "Qwen",
    "remote_url": "https://github.com/QwenLM/Qwen.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "2df8e8ac450fa185c421a08b0090ef81826caa6e",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [],
      "note": "The checkout has no top-level pyproject.toml, setup.py, or setup.cfg for a qwen distribution; it provides scripts, requirements, recipes, and model-side remote code."
    },
    {
      "name": "fastllm_pytools",
      "version": "0.0.1",
      "import_names": ["fastllm_pytools"],
      "scope": "optional dcu-support package"
    }
  ],
  "evidence": {
    "source_roots": ["dcu-support/package/fastllm_pytools"],
    "docs": ["README.md", "FAQ.md", "tech_memo.md", "tokenization_note.md", "eval/EVALUATION.md", "recipes/"],
    "examples": ["examples/", "cli_demo.py", "web_demo.py", "openai_api.py"],
    "tests": ["recipes/tests/"],
    "configs": ["requirements.txt", "requirements_web_demo.txt", "finetune/ds_config_zero2.json", "finetune/ds_config_zero3.json", "docker/"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this graph as stale.
- If the source tree is dirty beyond generated skill/review artifacts, inspect the changed paths before relying on detailed commands.
- Recheck dependency ranges, model names, remote-code APIs, CLI flags, training scripts, benchmark data layouts, and vendor support when source behavior changes.
- The repository is historical and model-side code is loaded through checkpoint `trust_remote_code`; refresh when checkpoint APIs or compatible Transformers ranges change.
