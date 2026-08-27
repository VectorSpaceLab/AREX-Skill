# Repository provenance

Read this before deciding whether the PDEBench operating skill still matches a
checkout or whether `refresh-repo-skill` is needed.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T18:43:39Z",
  "repository": {
    "name": "PDEBench",
    "remote_url": "https://github.com/pdebench/PDEBench.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "4ff3e3a4aa1561721b5571fa3a048a0a463e0568",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "pdebench",
      "version": "0.1.0",
      "import_names": ["pdebench"]
    }
  ],
  "evidence": {
    "source_roots": ["pdebench"],
    "docs": ["README.md", "pdebench/data_download/README.md", "pdebench/models/config/README.md"],
    "examples": ["pdebench/models/run_forward_1D.sh", "pdebench/models/run_inverse.sh", "pdebench/data_gen/data_gen_NLE/*/run_*.sh"],
    "tests": ["tests/test_vorticity.py"],
    "configs": ["pdebench/data_gen/configs", "pdebench/data_gen/data_gen_NLE/*/config", "pdebench/models/config"]
  }
}
```

## Refresh check

- If the current commit differs from `4ff3e3a4aa1561721b5571fa3a048a0a463e0568`,
  treat the skill as potentially stale and run `refresh-repo-skill`.
- This snapshot was made from a dirty checkout because the generated skill and
  its review artifacts live under `skills/`. Unexpected dirty paths should be
  reviewed separately; generated source files or dependency changes are not
  covered by this baseline.
- If package metadata, console entry points, model/config keys, HDF5 schemas, or
  the vorticity API change, refresh even when the commit is unchanged.
- The skill's published runtime files are self-contained; the source evidence
  paths above are provenance only and are not runtime dependencies.
