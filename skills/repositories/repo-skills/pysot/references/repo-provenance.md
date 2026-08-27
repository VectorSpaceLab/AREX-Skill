# Repository Provenance

## Purpose

Read this before deciding whether this PySOT skill is current for a checkout. If the current repo commit, dirty state, package metadata, public APIs, or major evidence paths differ from this snapshot, refresh the skill before relying on it.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T19:28:42Z",
  "repository": {
    "name": "pysot",
    "remote_url": "https://github.com/STVIR/pysot.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "d04028f8e18c6b27ee150a7c0d8aab9a1807219e",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "toolkit",
      "version": "0.0.0",
      "import_names": ["toolkit"]
    },
    {
      "name": "pysot",
      "version": null,
      "import_names": ["pysot"],
      "note": "The repository docs expose pysot through checkout/PYTHONPATH-style imports rather than setup.py package metadata."
    }
  ],
  "evidence": {
    "source_roots": ["pysot/", "toolkit/"],
    "docs": ["README.md", "INSTALL.md", "TRAIN.md", "MODEL_ZOO.md", "testing_dataset/README.md", "training_dataset/*/readme.md"],
    "configs": ["experiments/*/config.yaml"],
    "examples_and_tools": ["tools/demo.py", "tools/test.py", "tools/eval.py", "tools/train.py", "tools/hp_search.py", "demo/"],
    "optional_integrations": ["vot_iter/"]
  },
  "verification_baseline": {
    "safe_imports": ["pysot", "pysot.core.config", "pysot.models.model_builder", "pysot.tracker.tracker_builder", "toolkit", "toolkit.datasets", "toolkit.evaluation", "toolkit.utils.region"],
    "safe_cli_help": ["tools/demo.py", "tools/test.py", "tools/eval.py", "tools/train.py", "tools/hp_search.py"],
    "safe_smokes": ["cfg.merge_from_file on a sample experiment YAML", "ModelBuilder plus build_tracker construction on CPU", "toolkit.utils.region.vot_overlap simple overlap"],
    "not_verified": ["full demo tracking", "full benchmark test", "full metric evaluation", "full training", "hyperparameter search"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale and refresh it.
- If package metadata changes so that `pysot` becomes an installed distribution or `toolkit` build behavior changes, refresh install/import guidance.
- If `tools/demo.py`, `tools/test.py`, `tools/eval.py`, `tools/train.py`, `pysot/core/config.py`, model/tracker factories, toolkit datasets/evaluation modules, or experiment config conventions change, refresh the affected sub-skills.
- If a current checkout has different dirty source paths than this snapshot, inspect the changes before relying on config/model/tracking/evaluation details.
