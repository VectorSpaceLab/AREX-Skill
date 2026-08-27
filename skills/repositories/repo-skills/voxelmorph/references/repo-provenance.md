# Repository Provenance

## Purpose

Read this before deciding whether this VoxelMorph skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public APIs, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T11:58:45Z",
  "repository": {
    "name": "voxelmorph",
    "remote_url": "https://github.com/voxelmorph/voxelmorph.git",
    "vcs": "git",
    "branch": "dev",
    "tag": null,
    "commit": "e82b8ef768dceb4b6e8a9855ba9fa172e91b8c50",
    "working_tree": "dirty-untracked-skill-output",
    "dirty_paths": [
      "skills/voxelmorph.log",
      "skills/disco/voxelmorph/",
      "skills/tests/voxelmorph/"
    ]
  },
  "packages": [
    {
      "name": "voxelmorph",
      "version": "0.3.3",
      "import_names": ["voxelmorph"]
    },
    {
      "name": "neurite",
      "version": "0.3.2",
      "import_names": ["neurite"]
    },
    {
      "name": "torch",
      "version": "2.13.0+cpu",
      "import_names": ["torch"]
    }
  ],
  "evidence": {
    "package_metadata": ["pyproject.toml", "setup.py"],
    "source_roots": ["voxelmorph"],
    "docs": ["README.md", "docs/docs/index.md", "docs/mkdocs.yml"],
    "examples_and_scripts": ["scripts/train.py", "scripts/register.py"],
    "tests": [
      "tests/test_imports.py",
      "tests/test_functional.py",
      "tests/test_modules.py",
      "tests/test_models.py",
      "tests/test_neurite_integration.py"
    ],
    "configs": [".pre-commit-config.yaml", ".readthedocs.yaml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, public entry points, or the `voxelmorph.nn` / `voxelmorph.py` APIs changed, refresh even if the commit is close.
- If the current checkout exposes a legacy `vxm.networks` API, TensorFlow branch files, new CLI entry points, or different training/registration scripts, refresh this skill before using those surfaces.
- The snapshot was generated while untracked skill output existed under `skills/`; that does not indicate modified package source files, but it does mean the checkout was not VCS-clean at generation time.
