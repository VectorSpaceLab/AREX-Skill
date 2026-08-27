# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Cirq. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:26:53Z",
  "repository": {
    "name": "Cirq",
    "remote_url": "https://github.com/quantumlib/Cirq.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "53f45a4323eeb81b21fd0046f3ac4cdc914dde39",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"],
    "dirty_note": "Generated skill artifacts and the batch log were present under skills/. No source package files were modified for extraction."
  },
  "packages": [
    {"name": "cirq", "version": "1.8.0.dev0", "import_names": ["cirq", "cirq_google", "cirq_ionq", "cirq_aqt", "cirq_pasqal", "cirq_web"]},
    {"name": "cirq-core", "version": "1.8.0.dev0", "import_names": ["cirq"]},
    {"name": "cirq-google", "version": "1.8.0.dev0", "import_names": ["cirq_google"]},
    {"name": "cirq-ionq", "version": "1.8.0.dev0", "import_names": ["cirq_ionq"]},
    {"name": "cirq-aqt", "version": "1.8.0.dev0", "import_names": ["cirq_aqt"]},
    {"name": "cirq-pasqal", "version": "1.8.0.dev0", "import_names": ["cirq_pasqal"]},
    {"name": "cirq-web", "version": "1.8.0.dev0", "import_names": ["cirq_web"]}
  ],
  "evidence": {
    "source_roots": [
      "cirq-core/cirq",
      "cirq-google/cirq_google",
      "cirq-ionq/cirq_ionq",
      "cirq-aqt/cirq_aqt",
      "cirq-pasqal/cirq_pasqal",
      "cirq-web/cirq_web"
    ],
    "package_metadata": [
      "README.md",
      "setup.py",
      "pyproject.toml",
      "cirq-core/setup.py",
      "cirq-core/requirements.txt",
      "cirq-google/setup.py",
      "cirq-google/requirements.txt",
      "cirq-ionq/setup.py",
      "cirq-aqt/setup.py",
      "cirq-pasqal/setup.py",
      "cirq-web/setup.py"
    ],
    "docs": [
      "docs/start",
      "docs/build",
      "docs/simulate",
      "docs/transform",
      "docs/google",
      "docs/hardware",
      "docs/experiments"
    ],
    "examples": ["examples"],
    "tests": [
      "cirq-core/cirq/**/*_test.py",
      "cirq-google/cirq_google/**/*_test.py",
      "cirq-ionq/cirq_ionq/**/*_test.py",
      "cirq-aqt/cirq_aqt/**/*_test.py",
      "cirq-pasqal/cirq_pasqal/**/*_test.py",
      "cirq-web/cirq_web/**/*_test.py"
    ],
    "excluded_or_deprioritized": [
      "benchmarks",
      "dev_tools maintainer internals",
      "Node/frontend check scripts",
      "generated/cached/build artifacts",
      "live provider service calls requiring credentials"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source/package/doc/example/test changes beyond generated skill artifacts, refresh this skill.
- If Cirq package versions, public imports, provider signatures, or documented workflows change, refresh this skill even on the same commit.
- If a task depends on optional contrib integrations or live provider-service behavior not verified here, extend or refresh the relevant sub-skill before relying on it.
