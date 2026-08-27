# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an OpenFlamingo checkout or installed package. If the current repository commit, package metadata, public entrypoints, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:12:04Z",
  "repository": {
    "name": "open_flamingo",
    "remote_url": "https://github.com/mlfoundations/open_flamingo.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "655f693fbfa04cd6e9a987d960654624d48917cf",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "open_flamingo",
      "version": "2.0.1",
      "import_names": ["open_flamingo"]
    }
  ],
  "evidence": {
    "source_roots": ["open_flamingo", "open_flamingo/src"],
    "docs": ["README.md", "open_flamingo/train/README.md", "open_flamingo/eval/README.md", "docs/flamingo.png"],
    "training": ["open_flamingo/train", "open_flamingo/scripts/run_train.sh"],
    "evaluation": ["open_flamingo/eval", "open_flamingo/scripts/run_eval.sh", "open_flamingo/scripts/cache_rices_features.py"],
    "data_preparation": ["open_flamingo/scripts/convert_mmc4_to_wds.py", "open_flamingo/scripts/fill_vqa_testdev_results.py", "open_flamingo/eval/data"],
    "packaging": ["setup.py", "requirements.txt", "requirements-training.txt", "requirements-eval.txt", "environment.yml", "Makefile", ".pre-commit-config.yaml"]
  },
  "verification_summary": {
    "safe_import_and_signature_checks": "passed in private inspection environment",
    "safe_help_parser_checks": "passed for training, evaluation, RICES cache, MMC4 conversion, and VQA fill helpers",
    "full_generation_training_evaluation": "not executed; requires external checkpoints, datasets, network/cache, and GPU/time budget"
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package version, dependencies, public imports, train/eval script locations, or CLI flags changed, refresh even if the commit is close.
- If the installed package no longer includes `open_flamingo/train/train.py`, `open_flamingo/eval/evaluate.py`, or `open_flamingo/scripts/cache_rices_features.py`, refresh the wrappers and command-builder guidance.
- If the repository changes its dependency compatibility around `torch`, `transformers`, `numpy`, or `open_clip_torch`, refresh the root compatibility and troubleshooting references.
