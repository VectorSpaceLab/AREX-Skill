# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of NVlabs/MUNIT. If the current repo commit, dirty state, package/import surface, config files, or public entrypoints differ from this snapshot, run `refresh-repo-skill` before relying on the skill for new work.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T13:14:55Z",
  "repository": {
    "name": "MUNIT",
    "remote_url": "https://github.com/NVlabs/MUNIT.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "a82e222bc359892bd0f522d7a0f1573f3ec4a485",
    "working_tree": "dirty-generated-skills-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "munit-source",
      "version": null,
      "import_names": ["data", "networks", "utils", "trainer"]
    }
  ],
  "environment_evidence": {
    "documented_python": ["2.7", "3.6"],
    "documented_pytorch": "0.4.1",
    "documented_torchvision": "0.2.x",
    "documented_cuda": "9.x / CUDA 9.1 in docs",
    "inspection_status": "partial: imports, signatures, CLI help, and data-loader checks passed; actual CUDA training/inference blocked on current host"
  },
  "evidence": {
    "source_roots": ["data.py", "networks.py", "trainer.py", "utils.py"],
    "docs": ["README.md", "USAGE.md", "TUTORIAL.md", "Dockerfile", "docs/munit_assumption.jpg"],
    "entrypoints": ["train.py", "test.py", "test_batch.py"],
    "configs": ["configs/demo_edges2handbags_folder.yaml", "configs/demo_edges2handbags_list.yaml", "configs/edges2handbags_folder.yaml", "configs/edges2shoes_folder.yaml", "configs/summer2winter_yosemite256_folder.yaml", "configs/synthia2cityscape_folder.yaml"],
    "datasets": ["datasets/demo_edges2handbags/"],
    "scripts": ["scripts/demo_train_edges2handbags.sh", "scripts/demo_train_edges2shoes.sh", "scripts/demo_train_summer2winter_yosemite256.sh"],
    "tests_or_native_candidates": ["train.py --help", "test.py --help", "test_batch.py --help", "demo data-loader folder/list smoke"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current checkout has source/config/docs changes beyond generated skill artifacts, refresh before using this skill for exact command or API guidance.
- If package metadata or public entrypoints are added, removed, or renamed, refresh before import or publication.
- If a modernized MUNIT fork removes legacy CUDA/PyTorch constraints, refresh rather than editing this legacy skill in place.
