# Repository Provenance

## Purpose

Read this before deciding whether this Axolotl repo skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, CLI entry points, docs, examples, or config schema differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-22T00:00:00Z",
  "repository": {
    "name": "axolotl",
    "remote_url": "https://github.com/axolotl-ai-cloud/axolotl",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e86163dd332f3aad2f29de8fe44b6cfd5f74b22d",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "axolotl",
      "version": "0.17.0.dev",
      "import_names": ["axolotl"],
      "requires_python": ">=3.10",
      "console_scripts": ["axolotl"]
    }
  ],
  "evidence": {
    "source_roots": ["src/axolotl"],
    "docs": ["README.md", "FAQS.md", "docs/agents", "docs", "docs/dataset-formats"],
    "examples": ["examples", "deepspeed_configs"],
    "tests": ["tests/cli", "tests/core", "tests/prompt_strategies", "tests/utils", "tests/e2e"],
    "scripts": ["scripts", "docs/scripts"],
    "package_metadata": ["pyproject.toml", "VERSION"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the working tree has source, docs, examples, tests, or package-metadata changes beyond generated skill artifacts, run `refresh-repo-skill`.
- If `axolotl config-schema`, `axolotl agent-docs`, public CLI commands, optional dependency groups, or config validation behavior changed, run `refresh-repo-skill`.
- If a user reports Axolotl behavior that contradicts this skill, verify against the current installed package and refresh from repo evidence rather than patching only one reference.
