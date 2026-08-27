# Repository Provenance

## Purpose

Read this before deciding whether this operating graph matches a current
SiamTrackers checkout. If the commit, dirty state, package metadata, or major
evidence roots differ, refresh the repo skill before relying on implementation
claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T19:08:36Z",
  "repository": {
    "name": "SiamTrackers",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "248663fde6bf7c40190cf10ee396d5662919ecd3",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "toolkit",
      "version": null,
      "import_names": ["toolkit", "nanotrack", "got10k"]
    }
  ],
  "evidence": {
    "source_roots": [
      "NanoTrack/nanotrack",
      "NanoTrack/toolkit",
      "NanoTrack/got10k",
      "DaSiamRPN/DaSiamRPN",
      "SiamBAN/SiamBAN",
      "SiamCAR/SiamCAR",
      "SiamDW/SiamDW-FC",
      "SiamDW/SiamDW-RPN",
      "SiamFC/SiamFC",
      "SiamFCpp/SiamFCpp-pysot",
      "SiamFCpp/SiamFCpp-video_analyst",
      "SiamMask/SiamMask-pysot",
      "SiamRPN/SiamRPN",
      "SiamRPN/SiamRPN-pysot",
      "SiamRPNpp/SiamRPNpp",
      "TrTr/TrTr-pysot",
      "UpdateNet/UpdateNet-DaSiamRPN"
    ],
    "docs": [
      "README.md",
      "NanoTrack/README.md",
      "DaSiamRPN/README.md",
      "LightTrack/README.md",
      "Ocean/README.md",
      "SiamBAN/README.md",
      "SiamCAR/README.md",
      "SiamDW/README.md",
      "SiamFC/README.md",
      "SiamFCpp/README.md",
      "SiamFace/README.md",
      "SiamMask/README.md",
      "SiamRPN/README.md",
      "SiamRPNpp/README.md",
      "TrTr/README.md",
      "UpdateNet/README.md"
    ],
    "examples": [
      "NanoTrack/bin/demo.py",
      "NanoTrack/bin/train.py",
      "NanoTrack/bin/test.py",
      "NanoTrack/bin/eval.py",
      "NanoTrack/bin/hp_search.py",
      "NanoTrack/pytorch2onnx.py",
      "NanoTrack/cal_macs_params.py",
      "NanoTrack/cal_speed.py"
    ],
    "tests": [],
    "configs": [
      "NanoTrack/models/config/configv1.yaml",
      "NanoTrack/models/config/configv2.yaml",
      "NanoTrack/models/config/configv3.yaml",
      "NanoTrack/nanotrack/core/config.py",
      "requirements.txt",
      "NanoTrack/setup.py",
      "SiamCAR/SiamCAR/requirement.txt",
      "SiamFCpp/SiamFCpp-pysot/requirement.txt",
      "SiamFCpp/SiamFCpp-video_analyst/requirements.txt"
    ]
  }
}
```

## Verified runtime facts

- Core NanoTrack modules, config objects, model/tracker builders, dataset
  factory, and GOT-10k experiment imports were inspected with a live Python
  environment.
- `ModelBuilder()` has no constructor arguments; `NanoTracker(model)` owns
  `init` and `track`; the frame and bbox/result contracts are captured in the
  inference route.
- The host inspection backend exposed CUDA-enabled PyTorch and passed a
  one-element CUDA allocation on an A100-class device. This is preparation
  evidence only, not a claim that checkpoints, tracking, training, or
  benchmarks were reproduced.
- The checkout's prebuilt `toolkit.utils.region` binary was not accepted as
  portable evidence because it failed with a Python ABI symbol error. Fresh
  extension build/import remains a final verification case.

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the graph as
  potentially stale and run a refresh workflow.
- If this snapshot is dirty but the current `skills/` changes differ from the
  current checkout's generated artifacts, refresh before using the graph.
- If a source root, model config, public entry point, extension contract, or
  variant README changes, refresh the affected sub-skill even if the commit is
  unchanged in a copied working tree.
