# Repository Provenance

## Purpose

Read this before deciding whether the catalog router matches a later checkout.
If the commit, working-tree state, category counts, public entry-point
conventions, or major evidence paths differ, run `refresh-repo-skill` and
rebuild the bundled index before relying on routing claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T00:00:00Z",
  "repository": {
    "name": "medical-research-skills",
    "remote_url": "https://github.com/aipoch/medical-research-skills.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "f5ef65b9bea79b6dd9553f52f95b0d08f7d64d26",
    "working_tree": "dirty-after-generation",
    "dirty_paths": ["skills/ (generated runtime and review artifacts)"]
  },
  "packages": [],
  "evidence": {
    "source_roots": [],
    "docs": ["README.md", "skill-auditor/README.md"],
    "examples": ["scientific-skills/*/*/SKILL.md", "awesome-med-research-skills/*/*/SKILL.md"],
    "tests": ["skill-auditor/scripts/evaluate_skill.py", "selected per-skill parser/help candidates"],
    "configs": [".github/workflows/", "per-skill requirements.txt and assets where relevant"]
  }
}
```

## Public surface facts

- The repository is a public content catalog, not a root Python distribution.
- At this snapshot, the generated discovery index contains 604 source `SKILL.md`
  entries: 463 in `scientific-skills` and 141 in `awesome-med-research-skills`.
- The five category names are `Academic Writing`, `Data Analysis`, `Evidence
  Insight`, `Other`, and `Protocol Design`.
- Individual entries may contain their own scripts, references, requirements,
  assets, API access, credentials, external runtimes, data, or hardware.

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the router as
  stale and run `refresh-repo-skill`.
- If the source collection counts, category names, or representative public
  entry points change, rebuild `references/catalog-index.json` and rerun
  `scripts/check_catalog_skill.py`.
- If the working tree contains source changes rather than only generated
  artifacts, update the evidence map and verification plan before claiming
  coverage.
- Do not copy local checkout paths, private environment paths, API keys, cache
  locations, or command logs into public runtime content.
