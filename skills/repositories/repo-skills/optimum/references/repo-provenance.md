# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of Hugging Face Optimum. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T19:24:40Z",
  "repository": {
    "name": "optimum",
    "remote_url": "https://github.com/huggingface/optimum.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "787038e023d43f52fa599a71e5b0d0416d5c5c5f",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "optimum",
      "version": "2.4.0.dev0",
      "import_names": ["optimum"]
    }
  ],
  "evidence": {
    "package_metadata": ["setup.py", "pyproject.toml", "setup.cfg", "MANIFEST.in"],
    "source_roots": ["optimum"],
    "docs": [
      "README.md",
      "docs/source/index.mdx",
      "docs/source/installation.mdx",
      "docs/source/quicktour.mdx",
      "docs/source/exporters",
      "docs/source/torch_fx",
      "docs/source/llm_quantization",
      "docs/source/utils"
    ],
    "tests": [
      "tests/cli",
      "tests/exporters/common",
      "tests/fx/optimization",
      "tests/fx/parallelization",
      "tests/gptq",
      "tests/utils",
      "tests/common",
      "tests/pipelines"
    ],
    "workflow_evidence": [
      ".github/workflows/test_cli.yml",
      ".github/workflows/test_exporters_common.yml",
      ".github/workflows/test_pipelines.yml",
      ".github/workflows/test_fx_optimization.yml",
      ".github/workflows/test_fx_automatic_parallelism.yml",
      ".github/workflows/test_gptq.yml"
    ],
    "generated_skill_subskills": [
      "sub-skills/exporters-and-cli",
      "sub-skills/fx-graph-workflows",
      "sub-skills/gptq-quantization",
      "sub-skills/utilities-and-configs"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and this snapshot was clean, or the dirty paths differ from this snapshot, run `refresh-repo-skill`.
- If `setup.py`, CLI entry points, docs navigation, optional extras, or public module names changed, refresh before relying on this skill for new work.
- If partner packages moved APIs into or out of base `optimum`, refresh the exporter/CLI and pipeline routes.
- If tensor-parallel Python compatibility changes upstream, refresh the FX sub-skill before using its version-sensitive guidance.
