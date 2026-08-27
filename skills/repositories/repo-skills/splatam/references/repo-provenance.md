# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, dependency files, public configs, main scripts, dataset loaders, or utility APIs differ materially from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T12:45:13Z",
  "repository": {
    "name": "SplaTAM",
    "remote_url": "https://github.com/spla-tam/SplaTAM.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "da6bbcd24c248dc884ac7f49d62e91b841b26ccc",
    "working_tree": "dirty-generated-skills",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["datasets.gradslam_datasets", "utils", "scripts"]
    },
    {
      "name": "diff_gaussian_rasterization",
      "version": "0.0.0-pinned-git-commit",
      "import_names": ["diff_gaussian_rasterization"]
    }
  ],
  "evidence": {
    "source_roots": ["scripts", "viz_scripts", "utils", "datasets/gradslam_datasets"],
    "docs": ["README.md", "datasets/gradslam_datasets/README.md"],
    "examples": ["configs", "bash_scripts"],
    "tests": [],
    "configs": ["configs/data", "configs/iphone", "configs/replica", "configs/replica_v2", "configs/scannet", "configs/scannetpp", "configs/tum"],
    "dependency_files": ["environment.yml", "requirements.txt", "venv_requirements.txt", ".gitmodules"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale.
- If `scripts/splatam.py`, `scripts/iphone_demo.py`, `scripts/nerfcapture2dataset.py`, `scripts/post_splatam_opt.py`, `scripts/gaussian_splatting.py`, `scripts/eval_novel_view.py`, `scripts/export_ply.py`, `viz_scripts/`, `configs/`, `datasets/gradslam_datasets/`, `utils/`, or dependency files changed, refresh before relying on workflow details.
- If the custom rasterizer dependency commit or the documented Torch/CUDA compatibility changes, refresh environment guidance.
- Generated `skills/` dirty state is expected for this production checkout; do not treat it as source-code drift by itself.
