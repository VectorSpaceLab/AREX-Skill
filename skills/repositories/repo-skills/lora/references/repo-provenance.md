# Repository Provenance

Read this file before deciding whether the generated skill still matches a
checkout of LoRA. If the commit, package version, dirty paths, or major evidence
roots differ, run `refresh-repo-skill` rather than trusting the existing graph.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T14:35:29Z",
  "repository": {
    "name": "LoRA",
    "remote_url": "https://github.com/microsoft/LoRA.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "c4593f060e6a368d7bb5af5273b8e42810cdef90",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "loralib",
      "version": "0.1.2",
      "import_names": ["loralib"]
    }
  ],
  "evidence": {
    "source_roots": ["loralib"],
    "docs": ["README.md", "examples/NLU/README.md", "examples/NLG/README.md"],
    "examples": ["examples/NLU", "examples/NLG"],
    "tests": ["examples/NLU/examples/test_examples.py", "examples/NLU/tests"],
    "configs": ["setup.py", "examples/NLU/setup.py", "examples/NLU/environment.yml", "examples/NLG/requirement.txt"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` is not the recorded commit, treat the skill as
  potentially stale.
- If a clean checkout becomes dirty, or the dirty paths differ from this
  snapshot, refresh before making source-level claims.
- Refresh when `setup.py` changes the `loralib` version, supported Python range,
  public package name, or package layout.
- Refresh when the LoRA-specific model integration in the NLU examples or the
  GPT-2 model/data pipeline changes. The large upstream Transformers test suite
  is not a freshness signal for this focused skill unless its LoRA flags or
  model integration changes.
