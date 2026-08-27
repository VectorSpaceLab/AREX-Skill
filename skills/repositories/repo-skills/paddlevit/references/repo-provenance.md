# Repository provenance

Read this file before using the skill against a checkout that may differ from
its extraction baseline. If the commit, dirty state, or major evidence paths
differ, run `refresh-repo-skill` before trusting detailed claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-22T00:30:00Z",
  "repository": {
    "name": "PaddleViT",
    "remote_url": "omitted-private-or-unknown",
    "vcs": "git",
    "branch": "develop",
    "tag": null,
    "commit": "5ac7d89d4fd0e3235d055ff15d5b1b1315499d70",
    "working_tree": "clean-at-analysis",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "PaddleViT",
      "version": null,
      "import_names": []
    }
  ],
  "evidence": {
    "source_roots": [
      "image_classification/<model>",
      "object_detection/DETR",
      "object_detection/Swin",
      "object_detection/PVTv2",
      "semantic_segmentation/src",
      "self_supervised_learning/dino",
      "gan/transGAN",
      "gan/Styleformer",
      "facial_expression"
    ],
    "docs": [
      "README.md",
      "image_classification/README.md",
      "object_detection/DETR/README.md",
      "semantic_segmentation/README.md",
      "docs/paddlevit-config.md",
      "docs/paddlevit-amp.md",
      "docs/paddlevit-multi-gpu.md",
      "docs/paddlevit-export-en.md",
      "docs/paddlevit-port-weights.md"
    ],
    "examples": [
      "semantic_segmentation/demo/demo.py",
      "image_classification/BEiT/export_models.py",
      "image_classification/BEiT/infer_exported_models.py",
      "gan/transGAN/generate.py",
      "gan/Styleformer/generate.py"
    ],
    "tests": [
      "image_classification/MAE/tests",
      "image_classification/MobileViT/test_multi_scale_sampler.py",
      "object_detection/DETR/tests"
    ],
    "configs": [
      "image_classification/*/configs",
      "object_detection/*/configs",
      "semantic_segmentation/configs",
      "self_supervised_learning/dino/configs",
      "gan/*/configs"
    ]
  },
  "source_project_version": null,
  "notes": [
    "PaddleViT is a collection of standalone source-rooted projects and has no repository-level package metadata.",
    "The inspection environment proved paddlepaddle-gpu 2.6.2 and CUDA execution, but that dependency version is not a PaddleViT release version.",
    "The source predates current Paddle APIs; re-probe the selected model family before making a current-runtime claim."
  ]
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the commit above, treat this skill as
  potentially stale.
- If the checkout is dirty or the changed paths affect configs, source roots,
  model builders, data readers, entry scripts, or docs, refresh it.
- If a selected model family moved, new model directories were added, or the
  Paddle API changed, refresh the affected sub-skill even if the commit is
  unchanged in a copied artifact.
