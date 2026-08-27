# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the NLP-progress repository. If the current repo commit, dirty state, package/export utility behavior, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on the generated operating graph.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T10:25:48Z",
  "repository": {
    "name": "NLP-progress",
    "remote_url": "https://github.com/sebastianruder/NLP-progress.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "379f03ff7568b18bd9843490b84c94679f880a79",
    "working_tree": "dirty-generated-artifacts-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [],
  "package_note": "This repository is not an installable Python package. The selected Python workflow is the standard-library structured export utility.",
  "evidence": {
    "source_roots": [],
    "docs": [
      "README.md",
      "structured/README.md",
      "jekyll_instructions.md"
    ],
    "content": [
      "english/",
      "vietnamese/",
      "chinese/",
      "bengali/",
      "hindi/",
      "persian/",
      "russian/",
      "spanish/",
      "french/",
      "german/",
      "arabic/",
      "korean/",
      "nepali/",
      "portuguese/",
      "turkish/"
    ],
    "scripts": [
      "structured/export.py"
    ],
    "site": [
      "Gemfile",
      "_includes/table.html",
      "_includes/chart.html",
      "_config.yml",
      "CNAME"
    ],
    "metadata": [
      "CITATION.cff",
      "LICENSE"
    ],
    "excluded": [
      ".git/",
      "img/",
      "skills/"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the source Markdown directories, `README.md`, `structured/export.py`, or Jekyll support files changed, refresh the skill even when the branch name is unchanged.
- The recorded dirty path is the generated `skills/` output area created during production, not source evidence. If a future checkout has other dirty content paths, refresh before using this skill for source-accurate maintenance.
- If the repository becomes an installable package or changes the structured export CLI/schema, refresh the skill.
