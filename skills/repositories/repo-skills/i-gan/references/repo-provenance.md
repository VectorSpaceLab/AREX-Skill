# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an iGAN checkout. If
the current repo commit, dirty state, package metadata, or major evidence paths
differ from this snapshot, run `refresh-repo-skill` before relying on the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:25:23Z",
  "repository": {
    "name": "iGAN",
    "remote_url": "https://github.com/junyanz/iGAN.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "50cecd2209094f2cd0df44c3c412e36a596d349d",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["lib", "model_def", "ui"]
    }
  ],
  "evidence": {
    "source_roots": ["lib", "model_def", "ui", "train_dcgan", "constrained_opt.py", "constrained_opt_theano.py"],
    "docs": ["README.md", "train_dcgan/README.md"],
    "examples": ["generate_samples.py", "iGAN_main.py", "iGAN_script.py", "iGAN_predict.py", "pics/input_color.png", "pics/input_color_mask.png", "pics/input_edge.png", "pics/shoes_test.png"],
    "tests": [],
    "scripts": ["models/scripts/download_dcgan_model.sh", "models/scripts/download_alexnet.sh", "datasets/scripts/download_hdf5_dataset.sh", "train_dcgan/train_script.sh"],
    "configs": ["model_def/dcgan_theano_config.py", "train_dcgan/train_dcgan_config.py"]
  },
  "verification_scope": {
    "prepared_scope": "static command planning and checkout inspection",
    "native_runtime_execution": "not verified",
    "unverified_runtime_requirements": ["legacy Theano CUDA/cuDNN", "PyQt4 display stack", "pretrained DCGAN model files", "AlexNet pickle for projection", "HDF5 datasets for training"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
  potentially stale.
- If a checkout changes the top-level scripts, `model_def/`, `ui/`, `lib/`, or
  `train_dcgan/`, refresh the skill even if the repository name is unchanged.
- If packaging metadata or public entry points are added later, refresh the
  setup and import guidance because this snapshot found no installable Python
  distribution metadata.
- If native CUDA/PyQt4 execution is later verified, refresh the verification
  notes and native candidate map so future agents do not inherit the current
  static-only runtime stance.
