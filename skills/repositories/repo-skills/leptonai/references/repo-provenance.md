# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the LeptonAI repository. If the current repo commit, dirty state, package version, CLI entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T07:34:44Z",
  "repository": {
    "name": "leptonai",
    "remote_url": "https://github.com/leptonai/leptonai.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "2f36b2efa4f324b4c02c645cd73eb216eb22825a",
    "working_tree": "clean at source-analysis time before generated skill artifacts were written",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "leptonai",
      "version": "0.0.post1.dev1+g2f36b2e",
      "import_names": ["leptonai"],
      "entry_points": ["lep = leptonai.cli:lep"]
    }
  ],
  "evidence": {
    "source_roots": [
      "leptonai/",
      "leptonai/api/v2/",
      "leptonai/cli/",
      "leptonai/types/",
      "leptonai/util/"
    ],
    "docs": [
      "README.md",
      "example_usage.md",
      "docs/workflow.md",
      "CONTRIBUTING.md"
    ],
    "tests": [
      "leptonai/tests/",
      "leptonai/cli/tests/"
    ],
    "package_metadata": [
      "pyproject.toml"
    ],
    "existing_agent_guidance": [
      "plugins/lepton-cli/skills/lepton-cli/SKILL.md",
      "plugins/lepton-cli/skills/lepton-cli/references/workloads.md"
    ],
    "excluded_or_sampled_only": [
      ".github/",
      "assets/",
      "misc/benchmark/",
      "leptonai/bench/",
      "plugin marketplace manifests",
      "generated skill and review artifacts"
    ]
  },
  "verification_baseline": {
    "python": ">=3.9,<3.14; inspection used Python 3.11",
    "installed_distribution": "leptonai",
    "cli_entry_point": "lep",
    "backend_plan": "CPU/any local package import and CLI help; live DGX Cloud Lepton workspace operations require user credentials and were not run"
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale.
- If source files under `leptonai/`, `pyproject.toml`, public docs, CLI modules, API modules, or tests changed, refresh before relying on command/API specifics.
- If `lep --help`, `lep <group> --help`, or verified Python signatures disagree with this skill, trust the installed package and refresh the skill.
- If the package version resolves from a release tag rather than the development version above, confirm whether the command/API surface is still compatible.

## Notes

- This provenance intentionally omits local checkout paths, environment prefixes, Python executable paths, and private credential details.
- Generated `skills/` artifacts are not source evidence for repository behavior; they are the output of this construction run.
