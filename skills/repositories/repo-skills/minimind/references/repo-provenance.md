# Repository Provenance

Read this before deciding whether the MiniMind repo skill is current for a checkout. If the commit, dirty state, package metadata, tokenizer files, public entrypoints, or major evidence paths differ materially, use a repo-skill refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T16:34:22Z",
  "repository": {
    "name": "minimind",
    "remote_url": "https://github.com/jingyaogong/minimind.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "393e387e9ad99f0f04c296e4c5e7353f4444629f",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "minimind",
      "version": null,
      "import_names": ["model", "dataset", "trainer", "scripts"]
    },
    {
      "name": "transformers",
      "version": "4.57.6",
      "import_names": ["transformers"]
    },
    {
      "name": "datasets",
      "version": "3.6.0",
      "import_names": ["datasets"]
    },
    {
      "name": "torch",
      "version": "2.6.0+cu124",
      "import_names": ["torch"]
    }
  ],
  "evidence": {
    "source_roots": ["model", "dataset", "trainer", "scripts", "eval_llm.py"],
    "docs": ["README.md", "README_en.md", "dataset/dataset.md", "requirements.txt"],
    "examples": ["eval_llm.py", "scripts/eval_toolcall.py", "scripts/chat_api.py", "scripts/web_demo.py", "scripts/serve_openai_api.py", "scripts/convert_model.py"],
    "tests": [],
    "configs": ["model/tokenizer_config.json", "model/tokenizer.json", "requirements.txt"]
  }
}
```

## Refresh check

- If the current `git rev-parse HEAD` differs from `393e387e9ad99f0f04c296e4c5e7353f4444629f`, treat this skill as potentially stale.
- If the working tree is clean or its changed paths differ materially from the snapshot, refresh before relying on version-sensitive claims.
- Refresh when `model/model_minimind.py`, `model/model_lora.py`, `model/tokenizer_config.json`, `dataset/lm_dataset.py`, `trainer/`, `scripts/`, `eval_llm.py`, `requirements.txt`, or the README workflow sections change.
- The repository has no `pyproject.toml`, `setup.py`, or `setup.cfg`; the source modules were verified as a repository-local import surface rather than as a published distribution.
