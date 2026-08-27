# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of PySR. If the current repository commit, dirty state, package version, or public evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on detailed API guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T18:00:04Z",
  "repository": {
    "name": "PySR",
    "remote_url": "https://github.com/astroautomata/PySR.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "4f17f44fdff76be46e0a598f1404b8115320ff3f",
    "working_tree": "dirty-before-generation",
    "dirty_paths": ["skills/PySR.log"]
  },
  "packages": [
    {
      "name": "pysr",
      "version": "2.0.0-beta.1",
      "import_names": ["pysr"]
    }
  ],
  "evidence": {
    "source_roots": ["pysr/"],
    "docs": ["README.md", "docs/src/examples.md", "docs/src/options.md", "docs/src/operators.md", "docs/src/tuning.md", "docs/src/slurm.md", "docs/src/backend.md"],
    "examples": ["example.py", "examples/pysr_demo.ipynb"],
    "tests": ["pysr/test/test_main.py", "pysr/test/test_startup.py", "pysr/test/test_cli.py", "pysr/test/test_jax.py", "pysr/test/test_torch.py", "pysr/test/test_autodiff.py", "pysr/test/test_slurm.py"],
    "configs": ["pyproject.toml", "environment.yml", "pysr/juliapkg.json"],
    "existing_skills_evidence": ["skills/pysr/SKILL.md"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the commit above, treat this skill as potentially stale.
- If package metadata, public constructor signatures, generated docs, CLI commands, or Julia backend package requirements changed, refresh even if the commit appears close.
- If the working tree contains source or documentation edits beyond generated skill artifacts and logs, refresh before using the skill as a current repo baseline.
