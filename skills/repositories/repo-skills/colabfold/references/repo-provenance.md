# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of ColabFold. If the current repo commit, dirty state, package version, console scripts, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T08:20:00Z",
  "repository": {
    "name": "ColabFold",
    "remote_url": "https://github.com/sokrypton/ColabFold",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e809493da50dfa66fcbf0057ec17f5fdedecf8c6",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "colabfold",
      "version": "1.6.1",
      "import_names": ["colabfold"],
      "console_scripts": ["colabfold_batch", "colabfold_search", "colabfold_split_msas", "colabfold_relax"]
    }
  ],
  "evidence": {
    "source_roots": ["colabfold", "colabfold/mmseqs", "colabfold/alphafold"],
    "docs": ["README.md", "MsaServer/README.md", "colabfold/openstructure/README.md"],
    "examples": ["AlphaFold2.ipynb", "AlphaFold3_of3.ipynb", "batch/AlphaFold2_batch.ipynb", "beta/*.ipynb", "verbose/*.ipynb"],
    "tests": ["tests", "test-data"],
    "configs": ["pyproject.toml", "MsaServer/config.json"],
    "scripts": ["setup_databases.sh", "colabfold_search.sh", "MsaServer/setup-and-start-local.sh", "MsaServer/restart-systemd.sh", "utils/convert_deepfold_weights.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-skill-from-repo`.
- If the current working tree is dirty and this snapshot was clean, or the snapshot was dirty and dirty paths differ, run `refresh-skill-from-repo`.
- If `pyproject.toml`, console entry points, optional extras, CLI flags, or public workflow docs changed, refresh the skill before relying on generated guidance.
