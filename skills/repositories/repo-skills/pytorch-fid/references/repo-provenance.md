# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of
`pytorch-fid`. If the current repo commit, dirty state, package version, public
entry points, or major evidence paths differ from this snapshot, run
`refresh-repo-skill` before relying on the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:30:06Z",
  "repository": {
    "name": "pytorch-fid",
    "remote_url": "https://github.com/mseitzer/pytorch-fid.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "b9c18118d082cbd263c1b8963fc4221dc1cbb659",
    "working_tree": "clean-at-source-inspection; generated skills/ outputs untracked after construction",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "pytorch-fid",
      "version": "0.3.0",
      "import_names": ["pytorch_fid"],
      "entry_points": ["pytorch-fid = pytorch_fid.fid_score:main", "python -m pytorch_fid"]
    }
  ],
  "evidence": {
    "source_roots": ["src/pytorch_fid"],
    "docs": ["README.md"],
    "examples": [],
    "tests": ["tests/test_fid_score.py"],
    "configs": ["setup.py", "pyproject.toml", "noxfile.py", ".github/workflows/tests_full.yaml", ".github/workflows/tests_reduced.yaml"],
    "excluded": [".git", "skills/pytorch-fid.log", "generated skills/ artifacts"]
  }
}
```

## Evidence notes

The skill content was distilled from these public repository paths and installed
package facts:

- `setup.py`: distribution name, console script, version source, requirements
  (`numpy`, `pillow`, `scipy`, `torch`, `torchvision`).
- `README.md`: installation command, CLI usage, `--device`, `--dims`,
  `--save-stats`, and TensorFlow comparability caveat.
- `src/pytorch_fid/__init__.py`: package version `0.3.0`.
- `src/pytorch_fid/__main__.py`: module CLI delegation to `fid_score.main()`.
- `src/pytorch_fid/fid_score.py`: CLI parser, image extension set, public FID
  functions, statistics computation, `.npz` handling, and `--save-stats` flow.
- `src/pytorch_fid/inception.py`: `InceptionV3` constructor, feature-dimension
  block map, PyTorch/TorchVision compatibility handling, and FID weight URL use.
- `tests/test_fid_score.py`: behavior for Frechet-distance formula, directory
  statistics with a mock model, `.npz` stats loading, and supported image type
  loading.
- Installed inspection: imports, metadata, CLI help, CPU torch/torchvision, and
  dependency compatibility checks passed. A torch 2.2.1 CPU inspection context
  required a NumPy 1.x runtime (`numpy<2`) to avoid the NumPy 2 ABI warning.

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree contains source changes outside generated skill
  outputs, run `refresh-repo-skill`.
- If package metadata, import names, CLI flags, `.npz` layout,
  `InceptionV3.BLOCK_INDEX_BY_DIM`, TorchVision compatibility code, first-run
  weight behavior, or supported image extension filtering changed, run
  `refresh-repo-skill`.
