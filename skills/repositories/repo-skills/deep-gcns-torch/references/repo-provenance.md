# Repository Provenance

Read this before deciding whether the operating guide still matches a source
checkout. If the commit, dirty state, package facts, or major evidence paths
differ, refresh the repo skill before relying on its claims.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T09:30:00Z",
  "repository": {
    "name": "deep_gcns_torch",
    "remote_url": "https://github.com/lightaime/deep_gcns_torch.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "4f6681eee2290e217bda941b5536452a7c09decb",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "deep_gcns_torch-source",
      "version": null,
      "import_names": ["gcn_lib", "eff_gcn_modules", "utils"]
    }
  ],
  "evidence": {
    "source_roots": ["gcn_lib", "eff_gcn_modules", "utils"],
    "docs": ["README.md", "examples/*/README.md"],
    "examples": ["examples/modelnet_cls", "examples/sem_seg_dense", "examples/sem_seg_sparse", "examples/part_sem_seg", "examples/ppi", "examples/ogb", "examples/ogb_eff"],
    "tests": [],
    "configs": ["examples/*/config.py", "examples/ogb/*/args.py", "examples/ppi/opt.py"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `4f6681eee2290e217bda941b5536452a7c09decb`, treat this guide as potentially stale.
- If source files under `gcn_lib`, `eff_gcn_modules`, `utils`, or selected
  `examples/` paths change, refresh even when the commit is unchanged in a
  copied checkout.
- The source has no distribution metadata. Re-check public imports and parser
  behavior when the PyTorch/PyG stack changes.
- The `skills/` dirty path records production artifacts, not a source-code
  modification; future refresh decisions should compare the source evidence
  paths above.
