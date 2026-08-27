# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the XLNet repository. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, refresh the repo skill before relying on it for detailed operating guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T05:59:41Z",
  "repository": {
    "name": "xlnet",
    "remote_url": "https://github.com/zihangdai/xlnet.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "bbaa3a6fa0b3a2ee694e8cf66167434f9eca9660",
    "working_tree": "clean-source-baseline-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [
        "xlnet",
        "modeling",
        "function_builder",
        "model_utils",
        "data_utils",
        "run_classifier",
        "run_squad",
        "run_race",
        "train_gpu"
      ],
      "notes": "The repository has no setup.py, pyproject.toml, or requirements file; it is a legacy source-script TensorFlow 1.x checkout rather than an installable distribution."
    }
  ],
  "evidence": {
    "source_roots": [
      "xlnet.py",
      "modeling.py",
      "function_builder.py",
      "model_utils.py",
      "gpu_utils.py",
      "prepro_utils.py",
      "classifier_utils.py",
      "data_utils.py",
      "run_classifier.py",
      "run_squad.py",
      "run_race.py",
      "train.py",
      "train_gpu.py",
      "tpu_estimator.py",
      "squad_utils.py"
    ],
    "docs": [
      "README.md",
      "misc/race_example.md"
    ],
    "examples": [
      "notebooks/colab_imdb_gpu.ipynb",
      "scripts/prepro_squad.sh",
      "scripts/gpu_squad_base.sh",
      "scripts/tpu_squad_large.sh",
      "scripts/tpu_race_large_bsz8.sh",
      "scripts/tpu_race_large_bsz32.sh"
    ],
    "tests": [],
    "configs": []
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as potentially stale and refresh it.
- If the checkout has new package metadata, requirements files, public entry points, or changed task scripts, refresh even if the commit is close.
- If a future runtime uses a different TensorFlow major version, confirm compatibility with the root environment checker and the workflow troubleshooting references.
- The source baseline was clean before this generated skill was written; generated `skills/` files are not part of the upstream source baseline.
