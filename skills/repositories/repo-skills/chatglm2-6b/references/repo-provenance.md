# Repository Provenance

## Purpose

Read this before deciding whether this skill still matches a ChatGLM2-6B
checkout. If the commit, dirty state, package requirements, model-loading
contract, or major evidence paths differ, refresh the skill instead of relying
on stale commands.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T19:36:47Z",
  "repository": {
    "name": "ChatGLM2-6B",
    "remote_url": "https://github.com/zai-org/ChatGLM2-6B.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "cb8e8b43c0951b32614f25c03e1ab593a0603a1c",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {"name": "transformers", "version": "4.30.2", "import_names": ["transformers"]},
    {"name": "torch", "version": "2.13.0+cu130", "import_names": ["torch"]},
    {"name": "gradio", "version": "3.50.2", "import_names": ["gradio"]},
    {"name": "streamlit", "version": "1.24.0", "import_names": ["streamlit"]},
    {"name": "accelerate", "version": "1.14.0", "import_names": ["accelerate"]},
    {"name": "fastapi", "version": "0.141.1", "import_names": ["fastapi"]},
    {"name": "sse-starlette", "version": "3.4.8", "import_names": ["sse_starlette"]},
    {"name": "datasets", "version": "5.0.1", "import_names": ["datasets"]},
    {"name": "cpm_kernels", "version": "1.0.11", "import_names": ["cpm_kernels"]}
  ],
  "model_contract": {
    "public_id": "THUDM/chatglm2-6b",
    "load_api": "transformers.AutoTokenizer/AutoModel.from_pretrained with trust_remote_code=True",
    "weights_bundled": false,
    "local_distribution": null
  },
  "evidence": {
    "source_roots": ["cli_demo.py", "web_demo.py", "web_demo2.py", "utils.py", "api.py", "openai_api.py", "ptuning"],
    "docs": ["README.md", "README_EN.md", "FAQ.md", "MODEL_LICENSE", "ptuning/README.md", "evaluation/README.md"],
    "examples": ["cli_demo.py", "web_demo.py", "web_demo2.py", "ptuning/web_demo.py"],
    "tests": [],
    "configs": ["requirements.txt", "ptuning/deepspeed.json"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, refresh the skill.
- If the source working tree changes beyond the recorded dirty area, refresh
  before trusting command defaults.
- Recheck `requirements.txt`, model remote-code APIs, Gradio/Streamlit UI
  versions, API request models, and `ptuning/arguments.py` when upgrading
  dependencies or model revisions.
- This repository has no local Python distribution metadata; changes to the
  script set or model-loading contract are the primary staleness signals.
