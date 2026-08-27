# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of LLM Foundry. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T04:00:55Z",
  "repository": {
    "name": "llm-foundry",
    "remote_url": "https://github.com/mosaicml/llm-foundry.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "0cdb2f42962fcf861e58b236e9bd1c9964ba99a4",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "llm-foundry",
      "version": "0.23.0.dev0",
      "import_names": ["llmfoundry"],
      "console_scripts": ["llmfoundry"]
    }
  ],
  "evidence": {
    "source_roots": ["llmfoundry/"],
    "docs": ["README.md", "TUTORIAL.md", "llmfoundry/README.md", "scripts/data_prep/README.md", "scripts/train/README.md", "scripts/eval/README.md", "scripts/inference/README.md"],
    "examples_and_scripts": ["scripts/data_prep/", "scripts/train/", "scripts/eval/", "scripts/inference/", "scripts/misc/", "mcli/"],
    "tests": ["tests/"],
    "configs": ["scripts/train/yamls/", "scripts/eval/yamls/", "scripts/inference/benchmarking/yamls/", "mcli/"],
    "package_metadata": ["setup.py", "pyproject.toml"]
  },
  "verification_baseline": {
    "python_versions_considered": ["3.12", "3.11"],
    "selected_inspection_python": "3.11",
    "required_backend_scope": ["cpu", "any"],
    "optional_backend_smoke": ["torch cuda allocation"],
    "optional_backends_not_fully_verified": ["flash-attn", "TransformerEngine", "MegaBlocks", "FasterTransformer", "ROCm", "Intel Gaudi", "MosaicML platform credentials"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the commit above, treat the skill as potentially stale and run `refresh-repo-skill`.
- This provenance records the source checkout state before the generated `skills/` output was added. If source files outside generated skill/artifact directories are dirty, run `refresh-repo-skill`.
- If `setup.py`, console entry points, registry names, public CLI flags, or model/data/eval/inference signatures changed, run `refresh-repo-skill` even if the commit is unchanged.
- If a task needs optional accelerator support that was not fully verified here, prepare and verify that backend before relying on those advanced paths.
