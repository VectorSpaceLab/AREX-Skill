# Repository Provenance

## Purpose

Read this before deciding whether this Sacred repo skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T03:59:56Z",
  "repository": {
    "name": "sacred",
    "remote_url": "https://github.com/IDSIA/sacred.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "86865b03d05e83da35ca582392ca31777db88d11",
    "working_tree": "dirty-generated-artifacts-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "sacred",
      "version": "0.8.7",
      "import_names": ["sacred"]
    }
  ],
  "evidence": {
    "source_roots": ["sacred/", "sacred/config/", "sacred/observers/", "sacred/stflow/"],
    "metadata": ["setup.py", "setup.cfg", "pyproject.toml", "requirements.txt", "dev-requirements.txt", "tox.ini", "MANIFEST.in"],
    "docs": ["README.rst", "docs/quickstart.rst", "docs/experiment.rst", "docs/configuration.rst", "docs/command_line.rst", "docs/ingredients.rst", "docs/observers.rst", "docs/logging.rst", "docs/randomness.rst", "docs/settings.rst", "docs/tensorflow.rst"],
    "examples": ["examples/*.py"],
    "tests": ["tests/test_arg_parser.py", "tests/test_commands.py", "tests/test_config/", "tests/test_experiment.py", "tests/test_ingredients.py", "tests/test_run.py", "tests/test_observers/", "tests/test_metrics_logger.py", "tests/test_settings.py", "tests/test_stdout_capturing.py", "tests/test_dependencies.py", "tests/test_stflow/"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has source, docs, examples, tests, packaging, or optional-integration changes not reflected in this snapshot, run `refresh-repo-skill`.
- If package metadata or public signatures for `Experiment`, `Ingredient`, `Run`, observers, config, CLI options, settings, or stflow changed, run `refresh-repo-skill`.
- Generated `skills/` artifacts alone do not change Sacred runtime behavior, but a refreshed skill should update this provenance if the generated tree is intentionally replaced.
