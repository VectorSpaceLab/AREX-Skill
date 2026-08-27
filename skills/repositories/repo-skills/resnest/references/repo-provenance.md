# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of ResNeSt. If the current repo commit, dirty state, package metadata, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on detailed API/config guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-17T17:45:58Z",
  "repository": {
    "name": "ResNeSt",
    "remote_url": "https://github.com/zhanghang1989/ResNeSt.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "1dfb3e8867e2ece1c28a65c9db1cded2818a2031",
    "working_tree": "dirty-generated-skill-output",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "resnest",
      "version": "0.0.6b20260818",
      "version_note": "Editable inspection generated a date-suffixed local version from setup.py; the public release seed in setup.py is 0.0.6.",
      "import_names": [
        "resnest",
        "resnest.torch",
        "resnest.gluon",
        "resnest.d2"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "resnest/torch",
      "resnest/gluon",
      "resnest/d2",
      "resnest/utils.py",
      "hubconf.py"
    ],
    "docs": [
      "README.md",
      "ablation.md",
      "d2/README.md",
      "scripts/gluon/README.md"
    ],
    "configs": [
      "configs/Base-ResNet50.yaml",
      "d2/configs"
    ],
    "scripts": [
      "scripts/torch/verify.py",
      "scripts/torch/train.py",
      "scripts/gluon/verify.py",
      "scripts/gluon/train.py",
      "scripts/dataset/prepare_imagenet.py",
      "d2/train_net.py",
      "d2/datasets/prepare_coco.py"
    ],
    "tests": [
      "tests/test_torch.py",
      "tests/test_radix_major.py",
      "tests/test_gluon.py"
    ],
    "packaging": [
      "setup.py",
      ".github/workflows/unit_test.yml"
    ]
  },
  "verification_baseline": {
    "required_backend": "cpu for core PyTorch package/model/layer smoke",
    "optional_backends": [
      "cuda acceleration",
      "mxnet/gluon",
      "detectron2"
    ],
    "minimum_verified_surface": [
      "resnest distribution metadata",
      "resnest.torch import",
      "resnest50(pretrained=False) tiny forward",
      "SplAtConv2d tiny forward"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, model factory names, Detectron2 config fields, or public script semantics changed, refresh even if the commit is close.
- If Gluon/MXNet or Detectron2 support is removed, renamed, or ported to a new API surface, refresh the optional backend sub-skills before using them.
- If only generated skill files under `skills/` differ, that is expected for this construction run; compare source/package paths before declaring the ResNeSt API stale.
