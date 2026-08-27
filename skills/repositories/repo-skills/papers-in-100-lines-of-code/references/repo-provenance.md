# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
Papers-in-100-Lines-of-Code. If the current repo commit, source evidence layout,
or generated catalog differs from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T07:20:46Z",
  "repository": {
    "name": "Papers-in-100-Lines-of-Code",
    "remote_url": "https://github.com/MaximeVandegar/Papers-in-100-Lines-of-Code.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "af27efe121e78c7a288acb9a340df890cf30090d",
    "working_tree": "clean-at-evidence-capture",
    "dirty_paths": []
  },
  "packages": [],
  "evidence": {
    "source_roots": ["62 top-level paper implementation directories"],
    "docs": ["README.md", "*/README.md"],
    "examples": ["*/*.py as standalone educational implementation scripts"],
    "tests": [],
    "configs": ["*/requirements.txt"],
    "excluded": [".git/", ".github/ISSUE_TEMPLATE/", "generated review artifacts", "large generated result assets", "external downloaded datasets and model weights"]
  },
  "inspection": {
    "package_distribution": null,
    "import_names": [],
    "python_files_ast_parsed": 71,
    "readmes_discovered": 63,
    "function_or_class_symbols_discovered": 803
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as
  potentially stale and run `refresh-repo-skill`.
- If the repository adds or removes top-level implementation directories,
  per-paper READMEs, scripts, or requirements files, refresh the bundled
  implementation catalog.
- If a checkout contains substantial local edits to implementation scripts or
  requirements, refresh before relying on dependency/back-end guidance.
- Generated `skills/` files created by this skill are not source evidence for
  the upstream repository unless a future refresh explicitly targets them.
