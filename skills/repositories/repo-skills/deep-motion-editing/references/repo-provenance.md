# Repository Provenance

Read this before deciding whether the runtime skill is current for a checkout.
If the commit, dirty state, public entry points, or major evidence paths differ,
run the repository-skill refresh workflow.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-20T00:00:00Z",
  "repository": {
    "name": "deep-motion-editing",
    "remote_url": "https://github.com/DeepMotionEditing/deep-motion-editing.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "74fff8fb35e6378351d03fb14ee22fccae28b0bf",
    "working_tree": "dirty-after-skill-generation; source baseline was clean",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["utils", "retargeting script roots", "style_transfer script root"]
    }
  ],
  "evidence": {
    "source_roots": ["utils", "retargeting", "style_transfer", "blender_rendering"],
    "docs": ["README.md"],
    "examples": ["retargeting/demo.py", "retargeting/demo.sh", "style_transfer/demo.sh", "blender_rendering/example.bvh"],
    "tests": ["retargeting/test.py", "style_transfer/test.py"],
    "configs": ["retargeting/option_parser.py", "style_transfer/config.py", "style_transfer/global_info/*.yml"]
  }
}
```

## Refresh check

- Compare `git rev-parse HEAD` with the recorded commit.
- Treat changes to BVH parsers/writers, retargeting model/data modules,
  style-transfer config/loaders, Blender scripts, or README commands as a
  reason to refresh.
- The source snapshot has no setup metadata or distribution version. Do not
  infer a package version from the skill directory.
- The generated `skills/` subtree is skill output and artifact state; it is not
  evidence that the upstream source implementation changed.
