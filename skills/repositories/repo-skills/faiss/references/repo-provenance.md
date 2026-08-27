# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a Faiss checkout. If
the commit, dirty state, package version, public entry points, or major evidence
paths differ, use the repository-skill refresh workflow before relying on the
graph.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-23T00:00:00Z",
  "repository": {
    "name": "faiss",
    "remote_url": "https://github.com/facebookresearch/faiss.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "7059eaf7da7eddda62e71367e684d4bdedd7f94f",
    "working_tree": "dirty",
    "dirty_paths": ["skills/ (production artifacts)"],
    "dirty_state_note": "The source baseline was clean before this generated skill and its review artifacts were written."
  },
  "packages": [
    {
      "name": "faiss-cpu",
      "version": "1.15.0",
      "import_names": ["faiss"]
    }
  ],
  "evidence": {
    "source_roots": ["faiss", "faiss/python", "faiss/gpu", "faiss/gpu_metal", "faiss/svs", "c_api"],
    "docs": ["README.md", "INSTALL.md", "CHANGELOG.md", "c_api/INSTALL.md"],
    "examples": ["tutorial/python", "tutorial/cpp", "demos"],
    "tests": ["tests", "faiss/gpu/test", "faiss/gpu_metal/test"],
    "configs": ["pyproject.toml", "CMakeLists.txt", "faiss/CMakeLists.txt"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `7059eaf7da7eddda62e71367e684d4bdedd7f94f`, treat this graph as potentially stale.
- If the current dirty paths differ materially from the recorded production
  artifact state, refresh before relying on source-specific claims.
- If `pyproject.toml` changes the distribution/version, or the public Python
  wrappers, CMake backend flags, factory grammar, or major evidence paths move,
  refresh the repo skill even if the commit is unchanged.
- The runtime graph is intentionally self-contained: provenance paths identify
  evidence for refresh decisions, but normal Researcher use does not require
  reopening the source checkout.
