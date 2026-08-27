# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public APIs, training configs, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-12T16:43:42Z",
  "repository": {
    "name": "DALLE2-pytorch",
    "remote_url": "https://github.com/lucidrains/DALLE2-pytorch.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "680dfc4d93b70f9ab23c814a22ca18017a738ef6",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "dalle2-pytorch",
      "version": "1.15.6",
      "import_names": ["dalle2_pytorch"]
    }
  ],
  "evidence": {
    "source_roots": ["dalle2_pytorch"],
    "docs": ["README.md", "prior.md", "configs/README.md", "dalle2_pytorch/dataloaders/README.md"],
    "examples": ["README.md", "prior.md", "configs/train_decoder_config.example.json", "configs/train_prior_config.example.json"],
    "tests": ["Makefile", ".github/workflows/ci.yml", "configs/train_decoder_config.test.json", "test_data"],
    "configs": ["configs/train_decoder_config.example.json", "configs/train_decoder_config.test.json", "configs/train_prior_config.example.json"],
    "scripts": ["train_decoder.py", "train_diffusion_prior.py", "dalle2_pytorch/cli.py"],
    "package_metadata": ["setup.py", "MANIFEST.in", "dalle2_pytorch/version.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree has user changes touching package source, config classes, training launchers, dataloaders, trackers, CLI entry points, or docs listed above, run `refresh-repo-skill`.
- If `dalle2-pytorch` package version or public entry points change, refresh before trusting API signatures or launcher guidance.
- If a task targets a fork with materially different training scripts or configs, use this skill as background only and verify the fork-specific behavior before giving commands.
