# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an AlphaGPT checkout.
If the current repository commit, dirty state, package metadata, or major
evidence paths differ from this snapshot, run `refresh-repo-skill` before relying
on the skill for new work.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T06:40:00Z",
  "repository": {
    "name": "AlphaGPT",
    "remote_url": "https://github.com/imbue-bit/AlphaGPT.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "d851f2221dcaf4d53a707344f68ae6801e3e5af5",
    "working_tree": "dirty-generated-skill-artifacts",
    "dirty_paths": [
      "skills/disco/alpha-gpt/",
      "skills/tests/alpha-gpt/",
      "skills/AlphaGPT.log"
    ]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [
        "data_pipeline",
        "model_core",
        "execution",
        "strategy_manager",
        "dashboard"
      ],
      "note": "Source tree has requirements.txt but no pyproject.toml, setup.py, or distribution metadata."
    }
  ],
  "evidence": {
    "source_roots": [
      "data_pipeline/",
      "model_core/",
      "strategy_manager/",
      "execution/",
      "dashboard/"
    ],
    "docs": [
      "README.md",
      "CATREADME.md"
    ],
    "requirements": [
      "requirements.txt",
      "requirements-optional.txt"
    ],
    "examples_or_scripts": [
      "data_pipeline/run_pipeline.py",
      "model_core/engine.py",
      "strategy_manager/runner.py",
      "execution/trader.py",
      "dashboard/app.py",
      "lord/experiment.py",
      "times.py"
    ],
    "tests": [],
    "excluded_or_reference_only": [
      "assets/",
      "paper/20251226.pdf",
      "lord/experiment.py",
      "times.py"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If package metadata is added later, refresh the install/import guidance because
  the current skill assumes a source-tree import model.
- If the Solana dependency surface changes, refresh the live-strategy pin and
  execution-safety notes.
- If new tests, examples, notebooks, or docs appear, refresh the native candidate
  map before trusting old verification coverage.
