# Repository Provenance

Read this before using the skill against a changed XrayGLM checkout. If the
commit, dirty paths, dependency surface, or major evidence paths differ, run a
refresh/rebuild rather than assuming the operating graph is current.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-22T03:00:00Z",
  "repository": {
    "name": "XrayGLM",
    "remote_url": "https://github.com/WangRongsheng/XrayGLM",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a30173b61645fdc91eb746d17f8d85e909d08fdd",
    "working_tree": "dirty",
    "dirty_paths": ["skills/XrayGLM.log", "skills/disco/", "skills/tests/"]
  },
  "packages": [
    {
      "name": "SwissArmyTransformer",
      "version": "0.3.7 (inspection reference)",
      "import_names": ["sat"]
    },
    {
      "name": "XrayGLM source modules",
      "version": null,
      "import_names": ["model", "cli_demo", "web_demo", "finetune_XrayGLM", "lora_mixin"]
    }
  ],
  "evidence": {
    "source_roots": ["model", "cli_demo.py", "web_demo.py", "finetune_XrayGLM.py", "lora_mixin.py"],
    "docs": ["README.md", "checkpoints/README.md", "assets/train_cli.txt"],
    "examples": ["XrayGLM_inference.ipynb", "data/demo/dataset.json"],
    "tests": [],
    "configs": ["requirements.txt", "requirements_wo_ds.txt", "finetune_XrayGLM.sh"],
    "data": ["data/Xray/openi-zh.json", "data/openi-en.json", "data/openi-ch-random.json", "data/demo/dataset.json"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the recorded commit.
- If this snapshot's dirty paths are absent or new source files, requirements,
  entry points, model modules, data schemas, or launcher behavior changed, run
  a repository-skill refresh.
- Recheck the SAT/PyTorch/DeepSpeed/bitsandbytes compatibility matrix after
  dependency files change. The versions above are inspection evidence, not a
  promise that every future wheel or GPU supports this legacy code.
- Model weights, tokenizer caches, local datasets, and private environment
  paths are intentionally not part of provenance.
