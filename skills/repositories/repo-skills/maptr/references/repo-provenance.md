# Repository Provenance

Read this before deciding whether the MapTR skill matches a checkout. If the
commit, dirty state, package version, or major evidence paths differ, refresh
the skill before relying on implementation details.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T00:00:00Z",
  "repository": {
    "name": "MapTR",
    "remote_url": "https://github.com/hustvl/MapTR.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "a6872d8d9670bde17b4b01560f1221f88b443d55",
    "working_tree": "dirty-during-skill-generation",
    "dirty_paths": [],
    "dirty_path_summary": "Generated skill and private review changes were present during capture; exact local paths are intentionally omitted."
  },
  "packages": [
    {"name": "mmdet3d", "version": "0.17.2", "import_names": ["mmdet3d"]},
    {"name": "mmcv-full", "version": "1.4.0 (documented target)", "import_names": ["mmcv"]},
    {"name": "mmdet", "version": "2.14.0 (documented target)", "import_names": ["mmdet"]},
    {"name": "mmsegmentation", "version": "0.14.1 (documented target)", "import_names": ["mmseg"]},
    {"name": "MapTR plugin", "version": "source checkout plugin", "import_names": ["projects.mmdet3d_plugin"]}
  ],
  "evidence": {
    "source_roots": ["projects/mmdet3d_plugin", "mmdetection3d/mmdet3d"],
    "docs": ["README.md", "docs/install.md", "docs/prepare_dataset.md", "docs/train_eval.md", "docs/visualization.md"],
    "examples": [],
    "tests": ["projects/mmdet3d_plugin/maptr/modules/ops/geometric_kernel_attn/test.py"],
    "configs": ["projects/configs/maptr", "projects/configs/datasets", "projects/configs/_base_"],
    "tools": ["tools/create_data.py", "tools/data_converter/av2_converter.py", "tools/train.py", "tools/test.py", "tools/maptr", "tools/analysis_tools", "tools/misc/print_config.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the snapshot commit, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current working tree is dirty and the generated snapshot's dirty paths
  differ materially, refresh before relying on exact config or API details.
- If package metadata, plugin registrations, custom operators, public config
  families, dataset schemas, or CLI entry points change, refresh the skill.
- The README describes a `maptrv2` branch separately. This skill does not claim
  coverage of branch-only centerline/topology behavior; refresh or create a
  branch-specific skill if that becomes the target.
