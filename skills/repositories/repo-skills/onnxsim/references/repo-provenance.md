# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of ONNX Simplifier. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T04:43:11Z",
  "repository": {
    "name": "onnxsim",
    "remote_url": "https://github.com/onnxsim/onnxsim.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "6771722813318a575672d1839d5db6272cd21b7c",
    "working_tree": "dirty-generated-skill-output",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "onnxsim",
      "version": "0.7.3",
      "import_names": ["onnxsim"]
    }
  ],
  "evidence": {
    "package_metadata": ["pyproject.toml", "setup.py", "requirements.txt", "MANIFEST.in", "VERSION"],
    "source_roots": ["onnxsim/"],
    "native_bindings": ["onnxsim/capi/", "rust/", "CMakeLists.txt", "cmake/"],
    "docs": ["README.md", "CLAUDE.md", "docs/"],
    "scripts": ["scripts/check_version_sync.sh", "scripts/bump_binding_versions.sh", "scripts/build_npm_package.sh", "scripts/stage_npm_package.sh", "scripts/test_rust_package_standalone.sh", "scripts/convertmodel/"],
    "tests": ["tests/", ".github/workflows/"],
    "excluded_or_reference_only": ["third_party/", "bench/", "scripts/regression/", "scripts/qualcomm/", "scripts/yolo/", "scripts/rfdetr/", "imgs/"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the source checkout has code/config/doc changes beyond generated skill output under `skills/`, run `refresh-repo-skill`.
- If package metadata, `onnxsim.simplify` signature, CLI flags, CMake options, Rust/C API contracts, or web/npm packaging paths changed, run `refresh-repo-skill`.
- The snapshot was produced from a checkout where generated skill files made `skills/` dirty; do not treat that generated output alone as evidence that upstream ONNX Simplifier changed.
