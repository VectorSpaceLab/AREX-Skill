# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a DreamerV3 checkout.
If the current commit, dirty state, package version, or major evidence paths
differ from this snapshot, run `refresh-repo-skill` before relying on
version-sensitive guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T18:19:45Z",
  "repository": {
    "name": "dreamerv3",
    "remote_url": "https://github.com/danijar/dreamerv3.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "e3f02248693a79dc8b0ebd62c93683888ddaccfe",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "dirty_note": "The working tree contained generated skill/log artifacts under skills/ during creation; source evidence paths below were read from repository code and docs."
  },
  "packages": [
    {
      "name": "dreamer",
      "version": "3.3.1",
      "import_names": ["dreamerv3", "embodied"]
    }
  ],
  "evidence": {
    "source_roots": ["dreamerv3/", "embodied/core/", "embodied/envs/", "embodied/jax/", "embodied/run/"],
    "docs": ["README.md"],
    "examples": [],
    "tests": ["embodied/tests/", "embodied/perf/"],
    "configs": ["dreamerv3/configs.yaml", "baselines.yaml", "requirements.txt", "setup.py", "Dockerfile", "entrypoint.sh"],
    "scripts": ["plot.py", "scores/view.py"],
    "score_artifacts": ["scores/*.json.gz"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If public config blocks, package metadata, entry points, optional dependency
  lists, or the `dreamerv3`/`embodied` module layout changed, refresh even if the
  commit hash is close.
- If the current working tree is dirty outside generated skill or log artifacts,
  inspect those changes before using version-sensitive API, CLI, or config
  details.
- If `dreamer` package metadata no longer reports version `3.3.1`, refresh the
  skill or verify every affected command/reference before use.
