# Repository Provenance

## Purpose

Read this before deciding whether the `ml-from-scratch` repo skill is current for a checkout of ML-From-Scratch. If the current package version, source commit, public imports, constructor signatures, dependency behavior, or bundled workflow examples differ from this snapshot, refresh the skill from repository evidence.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T14:05:03Z",
  "repository": {
    "name": "ML-From-Scratch",
    "remote_url": "https://github.com/eriklindernoren/ML-From-Scratch.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "a2806c6732eee8d27762edd6d864e0c179d8e9e8",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "distribution_name": "mlfromscratch",
      "version": "0.0.4",
      "import_names": ["mlfromscratch"]
    }
  ],
  "evidence": {
    "metadata": [
      "setup.py",
      "setup.cfg",
      "requirements.txt",
      "MANIFEST.in"
    ],
    "docs": [
      "README.md"
    ],
    "source_roots": [
      "mlfromscratch/",
      "mlfromscratch/supervised_learning/",
      "mlfromscratch/unsupervised_learning/",
      "mlfromscratch/deep_learning/",
      "mlfromscratch/reinforcement_learning/",
      "mlfromscratch/utils/"
    ],
    "examples": [
      "mlfromscratch/examples/",
      "mlfromscratch/data/TempLinkoping2016.txt"
    ],
    "tests": []
  }
}
```

## Refresh checks

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If `mlfromscratch` reports a different distribution version, refresh API signatures and dependency guidance.
- If source changes alter constructors, exported package imports, data utility behavior, or example compatibility with current NumPy/Gym/scikit-learn releases, refresh this skill before relying on exact troubleshooting notes.
- This snapshot observed no first-party tests. The bundled smoke scripts are validation aids for the generated skill, not proof that every educational algorithm is numerically correct.
