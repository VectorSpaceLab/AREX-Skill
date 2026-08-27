# Repository Provenance

Read this before deciding whether this skill is current for a Surprise checkout. If the repository commit, tag, dirty state, package version, or major evidence paths change, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-14T20:03:36Z",
  "repository": {
    "name": "scikit-surprise",
    "remote_url": "https://github.com/NicolasHug/Surprise",
    "vcs": "git",
    "branch": "master",
    "tag": "v1.1.5",
    "commit": "93e1c30f3b2d15bdd0f2c4c816fbfce59f000fad",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "scikit-surprise",
      "version": "1.1.5",
      "import_names": ["surprise"]
    }
  ],
  "evidence": {
    "source_roots": [
      "surprise/",
      "surprise/model_selection/",
      "surprise/prediction_algorithms/"
    ],
    "docs": [
      "README.md",
      "doc/source/getting_started.rst",
      "doc/source/prediction_algorithms.rst",
      "doc/source/building_custom_algo.rst",
      "doc/source/model_selection.rst",
      "doc/source/accuracy.rst",
      "doc/source/FAQ.rst"
    ],
    "examples": [
      "examples/basic_usage.py",
      "examples/load_custom_dataset.py",
      "examples/load_from_dataframe.py",
      "examples/load_custom_dataset_predefined_folds.py",
      "examples/predict_ratings.py",
      "examples/k_nearest_neighbors.py",
      "examples/grid_search_usage.py",
      "examples/precision_recall_at_k.py",
      "examples/top_n_recommendations.py",
      "examples/serialize_algorithm.py"
    ],
    "tests": [
      "tests/test_reader.py",
      "tests/test_dataset.py",
      "tests/test_split.py",
      "tests/test_validation.py",
      "tests/test_search.py",
      "tests/test_algorithms.py",
      "tests/test_accuracy.py",
      "tests/test_dump.py",
      "tests/test_similarities.py",
      "tests/test_bsl_options.py",
      "tests/test_sim_options.py",
      "tests/test_SVD.py",
      "tests/test_NMF.py",
      "tests/test_co_clustering.py",
      "tests/test_zero_ratings.py"
    ],
    "configs": [
      "pyproject.toml",
      "setup.py",
      "MANIFEST.in"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as potentially stale and refresh it.
- If the dirty paths expand beyond `skills/`, check whether the changes affect public APIs, docs, tests, or package metadata before reusing this skill.
- If `surprise.__version__`, core dependencies, public imports, built-in dataset behavior, or CLI entry points change, refresh the generated skill.
- If a future checkout substantially rewrites any evidence path above, refresh before relying on the affected route.
