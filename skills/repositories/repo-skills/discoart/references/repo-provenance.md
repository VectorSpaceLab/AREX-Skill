# Repository Provenance

## Purpose

Read this before deciding whether this DiscoArt skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:38:35Z",
  "repository": {
    "name": "discoart",
    "remote_url": "https://github.com/jina-ai/discoart.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "03946299dd2781215a01c690c86ccd13e0f65c80",
    "working_tree": "clean-source-before-generated-skill-output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "discoart",
      "version": "0.12.2",
      "import_names": ["discoart"]
    }
  ],
  "evidence": {
    "source_roots": ["discoart"],
    "docs": ["README.md", "FEATURES.md", "CHANGELOG.md", "discoart.ipynb"],
    "configs": ["discoart/resources/default.yml", "discoart/resources/cut-schedules.yml", "discoart/resources/models.yml", "discoart/resources/flow.yml", "Dockerfile", "setup.py", "MANIFEST.in"],
    "tests": ["tests/test_api.py", "tests/test_config.py", "tests/test_prompts.py", "tests/conftest.py"],
    "scripts": ["scripts/generate-docstring.py", "scripts/black.sh", "scripts/devbot.sh", "scripts/get-all-test-paths.sh", "scripts/get-last-release-note.py", "scripts/release.sh"]
  }
}
```

## Refresh check

Refresh this skill when any of the following is true:

- `git rev-parse HEAD` differs from the recorded commit.
- The current source checkout has changes in the package, resources, docs, tests, setup metadata, Dockerfile, or public scripts that are not only generated skill output.
- `discoart.__version__` or distribution metadata differs from `0.12.2`.
- Public APIs, CLI parser commands, Jina endpoints, default config keys, prompt schema behavior, or model catalog entries changed.
- The repository moved to a new dependency stack that changes Python/PyTorch/Jina/DocArray compatibility.

## Evidence boundaries

This generated skill distilled public behavior from the evidence paths above. It intentionally excludes maintainer release automation, CI commit-lint/formatting internals, original README media assets, and generated review/test artifacts.
