# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an InternImage checkout. If the current repo commit, dirty state, package metadata, major config layout, or public workflow entry points differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T07:43:06Z",
  "repository": {
    "name": "InternImage",
    "remote_url": "https://github.com/OpenGVLab/InternImage.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "31c962dc6c1ceb23e580772f7daaa6944694fbe6",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "intern-image",
      "version": null,
      "import_names": [
        "classification.models",
        "detection.mmdet_custom",
        "segmentation.mmseg_custom"
      ]
    },
    {
      "name": "DCNv3",
      "version": "1.1",
      "import_names": ["DCNv3", "ops_dcnv3"]
    },
    {
      "name": "openlanev2",
      "version": "0.1.0",
      "import_names": ["openlanev2"]
    }
  ],
  "evidence": {
    "source_roots": [
      "classification/models",
      "classification/dataset",
      "classification/ops_dcnv3",
      "detection/mmcv_custom",
      "detection/mmdet_custom",
      "detection/ops_dcnv3",
      "segmentation/mmcv_custom",
      "segmentation/mmseg_custom",
      "segmentation/ops_dcnv3",
      "sam",
      "autonomous_driving/occupancy_prediction/projects",
      "autonomous_driving/Online-HD-Map-Construction/src",
      "autonomous_driving/openlane-v2/openlanev2",
      "autonomous_driving/openlane-v2/plugin",
      "tensorrt/modulated_deform_conv_v3"
    ],
    "docs": [
      "README.md",
      "README_CN.md",
      "classification/README.md",
      "classification/huggingface/README.md",
      "detection/README.md",
      "detection/configs/*/README.md",
      "segmentation/README.md",
      "segmentation/configs/*/README.md",
      "autonomous_driving/README.md",
      "autonomous_driving/occupancy_prediction/README.md",
      "autonomous_driving/Online-HD-Map-Construction/README.md",
      "autonomous_driving/openlane-v2/README.md",
      "autonomous_driving/openlane-v2/docs/devkit.md",
      "autonomous_driving/openlane-v2/docs/submission.md",
      "autonomous_driving/openlane-v2/docs/metrics.md",
      "autonomous_driving/openlane-v2/data/README.md"
    ],
    "examples": [
      "classification/extract_feature.py",
      "classification/huggingface/test.py",
      "detection/image_demo.py",
      "segmentation/image_demo.py",
      "sam/main_zero_shot_instance_seg.py"
    ],
    "tests": [
      "classification/ops_dcnv3/test.py",
      "detection/ops_dcnv3/test.py",
      "segmentation/ops_dcnv3/test.py",
      "autonomous_driving/openlane-v2/openlanev2/preprocessing/check.py"
    ],
    "configs": [
      "classification/configs",
      "detection/configs",
      "segmentation/configs",
      "autonomous_driving/occupancy_prediction/projects/configs/bevformer/bevformer_intern-s_occ.py",
      "autonomous_driving/Online-HD-Map-Construction/src/configs/vectormapnet_intern.py",
      "autonomous_driving/openlane-v2/plugin/mmdet3d/configs/internimage-s.py"
    ],
    "scripts": [
      "classification/main.py",
      "classification/main_deepspeed.py",
      "classification/main_accelerate.py",
      "classification/export.py",
      "classification/train_in1k.sh",
      "classification/train_in1k_deepspeed.sh",
      "detection/train.py",
      "detection/test.py",
      "detection/dist_train.sh",
      "detection/dist_test.sh",
      "detection/deploy.py",
      "segmentation/train.py",
      "segmentation/test.py",
      "segmentation/dist_train.sh",
      "segmentation/dist_test.sh",
      "segmentation/deploy.py",
      "autonomous_driving/*/tools/train.py",
      "autonomous_driving/*/tools/test.py"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current checkout has source/config/doc changes outside generated `skills/` artifacts, refresh before relying on command or API details.
- If the OpenMMLab dependency family, DCNv3 operator package, OpenLane-V2 devkit import behavior, or public model/config names changed, refresh even on the same commit.
- This skill was generated from a checkout whose only observed dirty path category was generated production material under `skills/`; source evidence files were treated as the commit baseline above.
