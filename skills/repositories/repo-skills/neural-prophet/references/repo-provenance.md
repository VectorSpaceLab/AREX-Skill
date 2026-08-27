# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of NeuralProphet. If the current repo commit, package metadata, public API, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T04:34:31Z",
  "repository": {
    "name": "neural_prophet",
    "remote_url": "https://github.com/ourownstory/neural_prophet.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "5e6b2314547334bbd5dbfc9cc5e019efcb3d67c5",
    "working_tree": "clean-source-baseline-before-generated-skill-output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "neuralprophet",
      "version": "1.0.0rc10",
      "import_names": ["neuralprophet"]
    }
  ],
  "evidence": {
    "source_roots": ["neuralprophet/"],
    "docs": ["README.md", "docs/source/contents.rst", "docs/source/tutorials/", "docs/source/how-to-guides/", "docs/source/code/"],
    "tests": ["tests/test_cli.py", "tests/test_unit.py", "tests/test_integration.py", "tests/test_event_utils.py", "tests/test_uncertainty.py", "tests/test_wrapper.py", "tests/test_save.py", "tests/test_plotting.py", "tests/test_glocal.py"],
    "fixtures": ["tests/test-data/"],
    "configs": ["pyproject.toml", "poetry.lock", "setup.cfg", ".github/workflows/tests.yml", ".github/workflows/metrics.yml"],
    "source_scripts": ["scripts/install_hooks.bash", "scripts/pre_commit.bash", "scripts/pre_push.bash", "scripts/neuralprophet_dev_setup.py"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale.
- If package version, public constructor/method signatures, optional extras, or Python/dependency constraints change, refresh the skill even on the same commit.
- If source evidence paths are removed or reorganized, refresh the skill.
- Generated `skills/` output created during this distillation is not source evidence for NeuralProphet behavior.
