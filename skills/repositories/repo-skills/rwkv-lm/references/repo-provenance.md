# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
RWKV-LM. If the current commit, dirty state, package/runtime facts, or major
evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T18:18:12Z",
  "repository": {
    "name": "RWKV-LM",
    "remote_url": "https://github.com/BlinkDL/RWKV-LM.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "952102498e9ed367ea0a59ee64106916d474d30f",
    "working_tree": "clean before generated skill output; current dirty paths are generated production artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "RWKV-LM repository",
      "version": null,
      "import_names": []
    },
    {
      "name": "rwkv",
      "version": "0.8.32",
      "import_names": ["rwkv"]
    }
  ],
  "evidence": {
    "source_roots": [
      "RWKV-v5/src",
      "RWKV-v7/train_temp/src",
      "RWKV-v8"
    ],
    "docs": [
      "README.md",
      "RWKV-v7/README.md",
      "RWKV-v7/train_temp/README.md",
      "RWKV-v8/README.md",
      "RWKV-8.md",
      "Research/rwkv7-g0-7.2b.md"
    ],
    "examples": [
      "RWKV-v7/rwkv_v7_demo.py",
      "RWKV-v7/rwkv_v7_demo_rnn.py",
      "RWKV-v7/rwkv_v7_demo_fast.py",
      "RWKV-v7/rwkv_v7_numpy.py",
      "RWKV-v7/run_rwkv7_qwen35.py",
      "RWKV-v7/run_rwkv7_context_parallelism.py",
      "RWKV-v8/251014_rosa_1bit_train.py",
      "RWKV-v8/251016_rosa_1bit_run.py",
      "RWKV-v8/251024_rosaQKV_run.py",
      "RWKV-v8/251105_reverse_run.py"
    ],
    "tests": [],
    "configs": [
      "RWKV-v5/requirements.txt",
      "RWKV-v7/train_temp/requirements.txt",
      "RWKV-v7/train_temp/demo-training-prepare.sh",
      "RWKV-v7/train_temp/demo-training-run.sh",
      "RWKV-v5/demo-training-prepare.sh",
      "RWKV-v5/demo-training-run.sh"
    ]
  }
}
```

## Refresh check

- Refresh if the RWKV-LM commit differs from the recorded commit.
- Refresh if the current repository introduces packaging metadata, new primary
  version directories, changed RWKV-7 `train_temp` flags, or new RWKV-8 scripts.
- Refresh if future runtime guidance depends on a different `rwkv` pip package
  API than the version recorded above.
