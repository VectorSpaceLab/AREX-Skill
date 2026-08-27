# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the modAL repository. If the current repo commit, dirty state, package version, public API modules, examples, or tests differ materially from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T00:00:00Z",
  "repository": {
    "name": "modAL",
    "remote_url": "https://github.com/modAL-python/modAL.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "bba6f6fd00dbb862b1e09259b78caf6cffa2e755",
    "working_tree": "dirty-generated-output-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "modAL-python",
      "version": "0.4.2",
      "import_names": [
        "modAL"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "modAL/",
      "modAL/models/",
      "modAL/utils/"
    ],
    "docs": [
      "README.md",
      "docs/source/content/models/",
      "docs/source/content/query_strategies/",
      "docs/source/content/apireference/"
    ],
    "examples": [
      "examples/active_regression.py",
      "examples/bagging.py",
      "examples/bayesian_optimization.py",
      "examples/bayesian_optimization_multidim.py",
      "examples/custom_query_strategies.py",
      "examples/ensemble.py",
      "examples/ensemble_regression.py",
      "examples/information_density.py",
      "examples/multilabel_svm.py",
      "examples/pool-based_sampling.py",
      "examples/pytorch_integration.py",
      "examples/pytorch_mc_dropout.py",
      "examples/query_by_committee.py",
      "examples/ranked_batch_mode.py",
      "examples/sklearn_workflow.py",
      "examples/stream-based_sampling.py"
    ],
    "tests": [
      "tests/core_tests.py",
      "tests/example_tests/"
    ],
    "package_metadata": [
      "setup.py",
      "setup.cfg"
    ]
  },
  "verification_baseline": {
    "required_backend": "cpu",
    "optional_backends_not_claimed": [
      "cuda",
      "keras/tensorflow"
    ],
    "known_compatible_dependency_floor": {
      "python": "3.11",
      "numpy": "1.23.5",
      "scipy": "1.10.1",
      "pandas": "1.5.3",
      "scikit-learn": "1.3.2",
      "setuptools": "<81",
      "torch": "2.13.0+cpu for optional dropout inspection",
      "skorch": "0.9.0"
    }
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata changes from `modAL-python==0.4.2`, refresh the skill before relying on signatures or compatibility notes.
- If current dirty paths include source, docs, examples, or tests beyond generated `skills/` output, refresh before using the skill for exact API guidance.
- If optional deep integrations are now first-class dependencies or CUDA/Keras workflows become required, refresh the backend plan and verification evidence.
