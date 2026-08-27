# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the
repository. If the current repo commit, dirty state, package metadata, public
entry points, or major evidence paths differ from this snapshot, run the Creator
`refresh-repo-skill` workflow rather than assuming this operating graph is still
accurate.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T10:29:11Z",
  "repository": {
    "name": "tensorflow-yolov4-tflite",
    "remote_url": "https://github.com/hunglc007/tensorflow-yolov4-tflite.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "9f16748aa3f45ff240608da4bd9b1216a29127f5",
    "working_tree": "dirty-production-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "tensorflow-yolov4-tflite",
      "version": null,
      "import_names": ["core"],
      "package_style": "script-checkout-no-python-distribution-metadata"
    },
    {
      "name": "tensorflow",
      "version_requirement": "2.3.0rc0 documented; 2.3.0 stable verified for CPU import during skill construction",
      "import_names": ["tensorflow"]
    },
    {
      "name": "opencv-python",
      "version_requirement": "4.1.1.26 documented; 4.1.2.30 verified for CPU import during skill construction",
      "import_names": ["cv2"]
    }
  ],
  "evidence": {
    "source_roots": ["core/"],
    "docs": ["README.md"],
    "python_entry_points": [
      "save_model.py",
      "convert_tflite.py",
      "convert_trt.py",
      "detect.py",
      "detectvideo.py",
      "evaluate.py",
      "benchmarks.py",
      "train.py"
    ],
    "support_scripts": [
      "scripts/coco_convert.py",
      "scripts/coco_annotation.py",
      "scripts/voc_annotation.py",
      "scripts/get_coco_dataset_2017.sh",
      "scripts/google_utils.py"
    ],
    "configs_and_data_formats": [
      "core/config.py",
      "data/classes/*.names",
      "data/anchors/*.txt",
      "data/dataset/*.txt"
    ],
    "evaluation": ["mAP/main.py", "mAP/extra/"],
    "android": ["android/app/build.gradle", "android/app/src/main/java/org/tensorflow/lite/examples/detection/tflite/YoloV4Classifier.java"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as
  potentially stale.
- If public script flags, `core.config`, `core.yolov4` decode/model functions,
  dataset formats, Android asset names, or documented dependency pins change,
  refresh the skill even if the commit comparison is not available.
- Ignore dirty production artifact paths such as a regenerated `skills/` tree
  when comparing source behavior, but do not ignore dirty source files under
  `core/`, top-level Python entry points, `scripts/`, `mAP/`, `data/classes/`,
  `data/anchors/`, or `android/`.
