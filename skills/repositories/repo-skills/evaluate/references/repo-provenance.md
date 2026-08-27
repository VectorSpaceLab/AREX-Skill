# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public APIs, docs, examples, tests, or dependency metadata differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "evaluate",
    "remote_url": "https://github.com/huggingface/evaluate.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a7dd338386a4fae9a1767e05eb9ef9479513d9e8",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "evaluate",
      "version": "0.4.7.dev0",
      "import_names": ["evaluate"]
    }
  ],
  "evidence": {
    "source_roots": ["src/evaluate"],
    "docs": ["README.md", "docs/source"],
    "module_repositories": ["metrics", "comparisons", "measurements"],
    "templates": ["templates"],
    "tests": ["tests"],
    "package_metadata": ["setup.py", "setup.cfg"],
    "ci_and_maintainer_context": ["Makefile", ".github/workflows", "CONTRIBUTING.md"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-skill-from-repo`.
- If package version, install requirements, extras, or console entry points change, refresh this skill.
- If `src/evaluate/loading.py`, `src/evaluate/module.py`, `src/evaluate/evaluator/`, `src/evaluate/commands/evaluate_cli.py`, `src/evaluate/hub.py`, or module directories change substantially, refresh this skill.
- If the CLI no longer imports `huggingface_hub.Repository`, update `sub-skills/hub-and-cli/references/troubleshooting.md` accordingly.
