# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a Tensorpack checkout.
If the current repo commit, dirty state, package version, dependency metadata, or
major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T06:55:22Z",
  "repository": {
    "name": "tensorpack",
    "remote_url": "https://github.com/tensorpack/tensorpack.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "1547a54e8546494614ca31c984a1bfd1d0e24b77",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "tensorpack",
      "version": "0.11",
      "import_names": ["tensorpack"]
    }
  ],
  "evidence": {
    "source_roots": [
      "tensorpack/"
    ],
    "docs": [
      "README.md",
      "docs/tutorial/",
      "docs/modules/",
      "docs/README.md"
    ],
    "examples": [
      "examples/README.md",
      "examples/basics/",
      "examples/ResNet/",
      "examples/ImageNetModels/",
      "examples/FasterRCNN/",
      "examples/GAN/",
      "examples/DeepQNetwork/",
      "examples/A3C-Gym/",
      "examples/CTC-TIMIT/",
      "examples/Char-RNN/",
      "examples/PennTreebank/",
      "examples/CaffeModels/",
      "examples/Saliency/",
      "examples/keras/"
    ],
    "scripts": [
      "scripts/README.md",
      "scripts/ls-checkpoint.py",
      "scripts/checkpoint-manipulate.py",
      "scripts/dump-model-params.py",
      "scripts/checkpoint-prof.py"
    ],
    "tests": [
      "tests/run-tests.sh",
      "tests/case_script.py",
      "tests/test_mnist.py",
      "tests/test_infogan.py",
      "tests/test_resnet.py",
      "tensorpack/dataflow/serialize_test.py",
      "tensorpack/dataflow/imgaug/imgaug_test.py",
      "tensorpack/models/models_test.py",
      "tensorpack/tfutils/unit_tests.py",
      "tensorpack/callbacks/param_test.py"
    ],
    "configs": [
      "setup.py",
      "setup.cfg",
      "tox.ini",
      ".github/workflows/workflow.yml"
    ]
  },
  "verification_scope": {
    "required_backend": "cpu",
    "verified_environment_summary": "Tensorpack 0.11 with TensorFlow CPU 2.12, OpenCV, LMDB, and HDF5 for package inspection and safe helper checks.",
    "optional_unverified_backends": [
      "CUDA/multi-GPU/Horovod/BytePS",
      "Caffe conversion",
      "COCO/Faster R-CNN",
      "Atari RL",
      "TIMIT speech preprocessing",
      "large ImageNet-style training"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If the current branch/tag or public package version changed, refresh before
  relying on API details.
- If package metadata, TensorFlow compatibility code, public module imports,
  example families, checkpoint utilities, or docs/tutorial content changed,
  refresh even if the version string stayed the same.
- If the current working tree is dirty and this snapshot was clean, or dirty
  paths differ from this snapshot, refresh before producing operational guidance.
