# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of GPT-Image2-Skill. If the current repo commit, dirty state, package version, CLI entry point, gallery index, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T12:43:48Z",
  "repository": {
    "name": "GPT-Image2-Skill",
    "remote_url": "https://github.com/wuyoscar/GPT-Image2-Skill.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "068dd9e24aadc8731e46f38548ca4dcd94515d35",
    "working_tree": "dirty",
    "dirty_paths": [
      "production log and generated skill/review outputs present; source evidence files unchanged during construction"
    ]
  },
  "packages": [
    {
      "name": "gpt-image-cli",
      "version": "0.2.0",
      "import_names": ["gpt_image_cli"],
      "console_scripts": ["gpt-image"]
    }
  ],
  "evidence": {
    "source_roots": ["src/gpt_image_cli"],
    "package_metadata": ["pyproject.toml"],
    "docs": ["README.md", "README.zh.md", "docs/community-prompt-index.md", "docs/community-prompt-picks.json"],
    "existing_skills": ["skills/gpt-image/SKILL.md", "skills/gpt-image/references", "skills/gpt-image/scripts/generate.py"],
    "plugin_metadata": [".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"],
    "maintainer_docs": ["CONTRIBUTING.md", "CHANGELOG.md", "SECURITY.md", "SUPPORT.md", ".github/PULL_REQUEST_TEMPLATE.md", ".github/ISSUE_TEMPLATE"]
  },
  "verification_baseline": {
    "environment_status": "ok",
    "real_openai_api_calls": "skipped-by-design",
    "required_backend": "python-cpu-plus-openai-sdk-import",
    "native_checks": ["CLI help", "package import", "argument validation", "bundled helper help/static checks"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If package metadata changes the `gpt-image-cli` version, dependencies, import package, Python requirement, or console script, refresh the root and `cli-and-api` references.
- If `src/gpt_image_cli/cli.py` changes flags, defaults, endpoint behavior, output handling, or exit codes, refresh `cli-and-api` and rerun CLI help/argument checks.
- If `skills/gpt-image/references/gallery.md` or category files change, refresh `prompt-gallery`.
- If contribution templates, plugin metadata, or repository layout change, refresh `repo-maintenance`.
- The dirty-state summary records generation artifacts and the production log from this construction run without making the public runtime skill depend on review artifact paths; future refreshes should distinguish generated outputs from source evidence changes.
