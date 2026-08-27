# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of `tf-faster-rcnn`. If the current repo commit, dirty state, package/build metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T18:01:11Z",
  "repository": {
    "name": "tf-faster-rcnn",
    "remote_url": "https://github.com/endernewton/tf-faster-rcnn.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "b4da911705925ec00e8359b76a2d7260f6d1d314",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "tf_faster_rcnn",
      "version": null,
      "import_names": [
        "model",
        "datasets",
        "layer_utils",
        "nets",
        "nms",
        "roi_data_layer",
        "utils"
      ],
      "notes": "Repository root is not installable; lib/setup.py defines native extension build metadata and hard-requires CUDA/nvcc."
    }
  ],
  "evidence": {
    "source_roots": ["lib"],
    "docs": ["README.md", "docker/Dockerfile.cuda-7.5", "docker/Dockerfile.cuda-8.0"],
    "examples": ["tools/demo.py", "data/demo", "data/imgs"],
    "scripts": ["data/scripts/fetch_faster_rcnn_models.sh", "experiments/scripts/train_faster_rcnn.sh", "experiments/scripts/test_faster_rcnn.sh", "experiments/scripts/convert_vgg16.sh"],
    "configs": ["experiments/cfgs"],
    "tests": [],
    "review_artifacts": "omitted from runtime skill"
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current checkout has source changes outside generated `skills/` outputs, rerun or refresh before trusting API/build details.
- If `lib/setup.py`, `lib/model/config.py`, `tools/*.py`, `experiments/scripts/*.sh`, `experiments/cfgs/*.yml`, or dataset loaders changed, refresh the relevant sub-skills.
- If the target environment changes from TensorFlow 1.x to a ported TensorFlow 2.x fork, refresh; this skill describes the TensorFlow 1.x source behavior.

## Verification Baseline

Skill construction verified CPU/source-level facts: config defaults and overrides, anchor generation shape, CPU NMS fixture behavior, dataset registry count, and network constructor signatures. It did not verify full CUDA native build, pretrained demo execution, dataset-wide evaluation, model training, or benchmark AP reproduction.
