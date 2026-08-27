# Repository provenance

Read this before deciding whether the skill is current. Refresh it when the
source commit, public entry points, dependency assumptions, or major evidence
paths change.

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T16:07:30Z",
  "repository": {
    "name": "BigGAN-PyTorch",
    "remote_url": "https://github.com/ajbrock/BigGAN-PyTorch.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "98459431a5d618d644d54cd1e9fceb1e5045648d",
    "working_tree": "dirty",
    "dirty_paths": ["skills/", "__pycache__/", "sync_batchnorm/__pycache__/"]
  },
  "packages": [
    {
      "name": "BigGAN-PyTorch repository modules",
      "version": null,
      "import_names": ["BigGAN", "BigGANdeep", "utils", "datasets", "inception_utils"]
    }
  ],
  "evidence": {
    "source_roots": ["BigGAN.py", "BigGANdeep.py", "layers.py", "datasets.py", "sync_batchnorm/"],
    "docs": ["README.md", "TFHub/README.md"],
    "examples": ["scripts/launch_*.sh", "scripts/sample_*.sh", "scripts/utils/prepare_data.sh"],
    "tests": ["sync_batchnorm/unittest.py"],
    "configs": ["utils.py", "make_hdf5.py", "calculate_inception_moments.py", "TFHub/converter.py"]
  }
}
```

## Refresh checks

- A different commit requires a refresh.
- The source checkout was dirty during production; generated skill files and
  Python cache debris are production artifacts, not source evidence.
- Recheck the old PyTorch 1.0.1 README baseline before claiming compatibility
  with a newer torch/torchvision release.
