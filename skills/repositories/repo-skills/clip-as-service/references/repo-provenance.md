# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of CLIP-as-service. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on stale API or runtime details.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T18:57:15Z",
  "repository": {
    "name": "clip-as-service",
    "remote_url": "https://github.com/jina-ai/clip-as-service.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "03410570d4398084f5ca5c88ad968248e0f3fc5d",
    "working_tree": "clean-before-generated-skill-output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "clip-client",
      "version": "0.8.4",
      "import_names": ["clip_client"]
    },
    {
      "name": "clip-server",
      "version": "0.8.4",
      "import_names": ["clip_server"]
    },
    {
      "name": "clip-as-service",
      "version": "0.8.4",
      "import_names": ["clip_client", "clip_server"]
    }
  ],
  "evidence": {
    "source_roots": ["client/clip_client", "server/clip_server"],
    "docs": ["README.md", "docs/index.md", "docs/user-guides/client.md", "docs/user-guides/server.md", "docs/user-guides/retriever.md", "docs/user-guides/faq.md", "docs/user-guides/benchmark.rst", "docs/hosting"],
    "tests": ["tests/test_client.py", "tests/test_simple.py", "tests/test_ranker.py", "tests/test_search.py", "tests/test_server.py", "tests/test_model.py", "tests/test_tensorrt.py", "tests/test_helper.py", "tests/test_tokenization.py", "tests/conftest.py"],
    "configs": ["server/clip_server/torch-flow.yml", "server/clip_server/onnx-flow.yml", "server/clip_server/tensorrt-flow.yml"],
    "scripts": ["scripts/benchmark.py", "scripts/onnx_helper.py", "scripts/get-requirements.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, import names, public client methods, server executor parameters, built-in Flow YAML shape, or optional extras change, run `refresh-repo-skill` even on the same commit.
- This snapshot records the source checkout before generated skill files were added under `skills/`; generated skill output itself is not part of the source evidence baseline.
- Do not copy local environment paths, package installation locations, or cache directories into public refresh notes.
