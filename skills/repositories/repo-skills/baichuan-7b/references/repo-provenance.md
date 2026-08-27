# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a Baichuan-7B checkout. If the current repo commit, dirty state, dependency pins, public workflow files, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T07:38:49Z",
  "repository": {
    "name": "Baichuan-7B",
    "remote_url": "https://github.com/baichuan-inc/Baichuan-7B.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "6f3ef4633a90c2d8a3e0763d0dec1b8dc11588f5",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {"name": "torch", "version": "2.0.0", "import_names": ["torch"]},
    {"name": "transformers", "version": "4.29.1", "import_names": ["transformers"]},
    {"name": "xformers", "version": "0.0.20", "import_names": ["xformers"]},
    {"name": "deepspeed", "version": "0.9.2", "import_names": ["deepspeed"]},
    {"name": "sentencepiece", "version": "0.1.97", "import_names": ["sentencepiece"]},
    {"name": "numpy", "version": "1.23.5", "import_names": ["numpy"]},
    {"name": "datasets", "version": null, "import_names": ["datasets"]},
    {"name": "pandas", "version": null, "import_names": ["pandas"]}
  ],
  "evidence": {
    "source_roots": ["models/configuration_baichuan.py", "models/modeling_baichuan.py"],
    "docs": ["README.md", "README_EN.md", "LICENSE"],
    "examples": ["README.md#inference", "README.md#training", "README.md#benchmark"],
    "tests": [],
    "configs": ["config/deepspeed.json", "config/hostfile"],
    "scripts": ["train.py", "scripts/train.sh", "evaluation/evaluate_zh.py", "evaluation/evaluate_mmlu.py"],
    "requirements": ["requirements.txt"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale.
- If a future checkout changes `models/`, `train.py`, `evaluation/`, `config/`, `scripts/train.sh`, `requirements.txt`, or README workflow sections, refresh this skill before relying on detailed commands or troubleshooting.
- If the repo adds packaging metadata, official CLIs, tests, or safer maintained examples, refresh to replace source-derived assumptions and helper scripts.
- If dependency pins or Hugging Face remote-code behavior change, refresh the API and troubleshooting references.

## License Notes

The repository source code is Apache-2.0. The Baichuan-7B model weights have a separate model license referenced by the upstream project; check the model source and user intent before commercial use, redistribution, or derivative-weight handling.
