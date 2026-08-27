# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of NuPIC legacy. If the current repo commit, dirty state, package version, dependency surface, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on the skill for new work.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T05:55:50Z",
  "repository": {
    "name": "nupic-legacy",
    "remote_url": "https://github.com/numenta/nupic-legacy.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "7281482def2a96fbda663e6c39e8351a1886dec7",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The untracked skills/ tree contains generated skill and review artifacts from this construction run; no source-code changes were used as source evidence."
  },
  "packages": [
    {
      "name": "nupic",
      "version": "1.0.6.dev0",
      "import_names": ["nupic"]
    },
    {
      "name": "nupic.bindings",
      "version": "1.0.6",
      "import_names": ["nupic.bindings"]
    }
  ],
  "runtime_baseline": {
    "python": "2.7",
    "required_backend": "cpu",
    "required_compiled_dependencies": ["nupic.bindings", "numpy", "pycapnp/capnproto"],
    "optional_services": ["MySQL-compatible service for full swarming"]
  },
  "evidence": {
    "package_metadata": ["setup.py", "setup.cfg", "requirements.txt", "requirements-dev.txt", "VERSION", "MANIFEST.in"],
    "source_roots": ["src/nupic"],
    "docs": ["README.md", "DEPENDENCIES.md", "docs/source", "docs/examples"],
    "examples": ["examples/sp", "examples/tm", "examples/network", "examples/opf", "examples/swarm", "examples/prediction"],
    "tests": ["tests/unit", "tests/integration", "tests/swarming", "tests/regression"],
    "scripts": ["scripts/run_opf_experiment.py", "scripts/run_swarm.py", "scripts/run_experiment_classifier_diff.py", "scripts/temporal_memory_performance_benchmark.py", "scripts/profiling"],
    "excluded_or_reference_only": ["external", "ci", ".circleci", "coreos-vagrant", "Dockerfile*", "docs/source/_static", "profiling/benchmarks by default"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale and run `refresh-repo-skill`.
- If source files, docs, examples, package metadata, dependency pins, or public APIs changed even on the same commit, run `refresh-repo-skill`.
- If the current checkout has dirty source-code paths outside generated skill/review artifacts, run `refresh-repo-skill` before relying on the skill.
- If NuPIC is ported to Python 3 or the dependency pins are modernized, refresh every sub-skill because the current graph assumes Python 2.7 legacy behavior.
