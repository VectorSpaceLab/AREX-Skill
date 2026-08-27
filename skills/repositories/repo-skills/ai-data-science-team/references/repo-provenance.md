# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public modules, examples, or app workflows differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T08:23:51Z",
  "repository": {
    "name": "ai-data-science-team",
    "remote_url": "https://github.com/business-science/ai-data-science-team.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "4ffeb7f38178aa250917f29b01355f8b89ba809e",
    "working_tree": "clean-source-snapshot-before-generated-skill-files",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "ai-data-science-team",
      "version": "0.0.0.9017",
      "import_names": ["ai_data_science_team"]
    }
  ],
  "evidence": {
    "metadata": ["setup.py", "requirements.txt", "apps/*/requirements.txt"],
    "source_roots": [
      "ai_data_science_team/agents",
      "ai_data_science_team/ds_agents",
      "ai_data_science_team/ml_agents",
      "ai_data_science_team/multiagents",
      "ai_data_science_team/tools",
      "ai_data_science_team/templates",
      "ai_data_science_team/parsers",
      "ai_data_science_team/utils"
    ],
    "docs": ["README.md", "apps/README.md", "apps/*/README.md", "examples/README.md"],
    "examples": ["examples/**/*.ipynb", "apps/*/app.py"],
    "fixtures": ["data/*.csv", "data/northwind.db"],
    "secondary_notes": ["planning_docs"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale.
- If package metadata, optional extras, public imports, constructor signatures, response keys, Streamlit app structure, or notebook workflows changed, refresh the skill even if the commit is similar.
- If optional dependencies or provider APIs changed substantially, re-run the environment and smoke checks before trusting ML/EDA/app guidance.
- Generated skill files themselves are not source evidence; use source paths above when comparing repository changes.
