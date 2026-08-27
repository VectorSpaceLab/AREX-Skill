# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T13:09:41Z",
  "repository": {
    "name": "learning-to-learn",
    "remote_url": "https://github.com/google-deepmind/learning-to-learn.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "f3c1a8d176b8ea7cc60478bfcfdd10a7a52fd296",
    "working_tree": "dirty-untracked-production-artifacts",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["meta", "networks", "preprocess", "problems", "util"]
    }
  ],
  "runtime_dependencies_verified": [
    {"name": "tensorflow", "version": "1.15.5"},
    {"name": "dm-sonnet", "version": "1.36"},
    {"name": "numpy", "version": "1.18.5"},
    {"name": "dill", "version": "0.3.7"},
    {"name": "mock", "version": "5.2.0"},
    {"name": "nose-parameterized", "version": "0.6.0"},
    {"name": "protobuf", "version": "3.19.6"}
  ],
  "evidence": {
    "source_roots": ["meta.py", "networks.py", "preprocess.py", "problems.py", "util.py"],
    "docs": ["README.md", "CONTRIBUTING", "LICENSE"],
    "scripts": ["train.py", "evaluate.py"],
    "tests": ["convergence_test.py", "meta_test.py", "networks_test.py", "preprocess_test.py", "problems_test.py"],
    "configs": []
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the source files, CLI scripts, README problem list, or tests named above changed, refresh the skill.
- If the repository becomes an installable Python distribution or changes TensorFlow/Sonnet major versions, refresh the install and troubleshooting guidance.
- Ignore differences limited to generated `skills/` production artifacts unless the runtime skill itself is being refreshed.
