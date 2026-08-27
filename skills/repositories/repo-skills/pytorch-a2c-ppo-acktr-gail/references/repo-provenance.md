# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:10:00Z",
  "repository": {
    "name": "pytorch-a2c-ppo-acktr-gail",
    "remote_url": "https://github.com/ikostrikov/pytorch-a2c-ppo-acktr-gail.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "41332b78dfb50321c29bade65f9d244387f68a60",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "a2c-ppo-acktr",
      "version": "0.0.1",
      "import_names": ["a2c_ppo_acktr"]
    }
  ],
  "evidence": {
    "source_roots": ["a2c_ppo_acktr/"],
    "docs": ["README.md", "gail_experts/README.md"],
    "examples": ["main.py", "enjoy.py", "evaluation.py", "generate_tmux_yaml.py", "run_all.yaml", "visualize.ipynb"],
    "configs": ["setup.py", "requirements.txt"],
    "artifacts_sampled": ["logs/", "time_limit_logs/", "imgs/"],
    "excluded_runtime_sources": [".git/", "skills/tests/", "skills/*.log", "large historical monitor CSVs"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, parser flags, or public files such as `main.py`, `enjoy.py`, `gail_experts/convert_to_pytorch.py`, or `a2c_ppo_acktr/` changed, refresh even if the commit appears similar.
- The dirty path recorded here is local `skills/` production output, not a selected package source directory. If source files are dirty in a future checkout, refresh before relying on command/API details.
