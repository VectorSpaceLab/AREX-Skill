# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of ESPnet. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T16:08:19Z",
  "repository": {
    "name": "espnet",
    "remote_url": "https://github.com/espnet/espnet.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "870554ac258caf2e6eb7074863d53b4f299ba223",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {"name": "espnet", "version": "202604", "import_names": ["espnet2", "espnet3", "egs3"]}
  ],
  "evidence": {
    "source_roots": ["espnet2", "espnet3", "egs3"],
    "docs": ["README.md", "doc/installation.md", "doc/espnet2_tutorial.md", "doc/espnet2_training_option.md", "doc/espnet2_format_wav_scp.md", "doc/espnet2_distributed.md", "doc/parallelization.md", "doc/espnet3_tutorial.md"],
    "recipes": ["egs2/TEMPLATE", "egs2/mini_an4"],
    "tests": ["test/espnet2", "test/espnet3", "ci"],
    "tools": ["tools/check_install.py", "tools/installers", "tools/setup_*.sh"]
  }
}
```

## Refresh Check

If commit, package metadata, task modules, recipe template structure, or ESPnet3 stage behavior changed, refresh this skill.
