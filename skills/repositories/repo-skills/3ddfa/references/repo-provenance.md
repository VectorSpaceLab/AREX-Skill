# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of 3DDFA. If the current commit, dirty state, package layout, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:40:12Z",
  "repository": {
    "name": "3DDFA",
    "remote_url": "https://github.com/cleardusk/3DDFA.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "3545f355bfc71e5748fa915b13932958363135d7",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["mobilenet_v1", "utils", "vdc_loss", "wpdc_loss"]
    }
  ],
  "evidence": {
    "source_roots": ["mobilenet_v1.py", "utils/", "vdc_loss.py", "wpdc_loss.py"],
    "docs": ["readme.md", "c++/readme.md", "demo@obama/readme.md", "utils/cython/readme.md", "BFM_Remove_Neck/readme.md"],
    "examples": ["main.py", "video_demo.py", "speed_cpu.py", "samples/", "demo@obama/", "visualize.py"],
    "tests": [],
    "configs": ["requirements.txt", "train.configs/", "test.configs/", "visualize/tri.mat", "models/phase1_wpdc_vdc.pth.tar", "c++/weights/"],
    "training_and_evaluation": ["train.py", "training/", "benchmark.py", "benchmark_aflw.py", "benchmark_aflw2000.py"],
    "cpp_port": ["c++/CMakeLists.txt", "c++/*.cpp", "c++/*.h", "c++/convert_to_onnx.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current dirty paths differ materially from `dirty_paths`, refresh before trusting command, data, or API details.
- If the repository gains packaging metadata, public CLI entry points, or changes the default checkpoint/resources, refresh the skill.
- If moving from legacy 3DDFA to 3DDFA_V2, create or load a separate skill; do not assume this one covers the newer repository.
