# Repository provenance

Read this file before deciding whether the DLTK skill is current for a
checkout or installed package. If the commit, package version, or public API
surface changes, refresh the skill rather than assuming compatibility.

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-21T14:13:14Z",
  "repository": {
    "name": "DLTK",
    "remote_url": "https://github.com/DLTK/DLTK.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "f94d3bb509eb0741164149acbef0788769a869e4",
    "working_tree": "source-clean-at-baseline; generated skill and review artifacts are separate",
    "dirty_paths_at_baseline": []
  },
  "packages": [
    {
      "name": "dltk",
      "version": "0.2.1",
      "import_names": ["dltk"]
    }
  ],
  "evidence": {
    "source_roots": ["dltk/"],
    "docs": ["README.md", "CHANGELOG.md", "docs/source/"],
    "examples": ["examples/tutorials/", "examples/applications/"],
    "tests": ["tests/test_activations.py", "tests/test_sliding_window_segmentation.py"],
    "requirements": ["setup.py", "requirements.txt", ".travis.yml"],
    "utilities": ["dltk/utils.py"],
    "reference_only": ["data/ downloaders", "docs/key.enc", "CI/release deployment", "binary assets"]
  }
}
```

## Refresh signals

- The source commit or package version differs from the snapshot.
- Public signatures of `Reader`, preprocessing helpers, network builders,
  losses/metrics, or `sliding_window_segmentation_inference` change.
- TensorFlow 1.x symbols are removed or a workflow is ported to TensorFlow 2.
- Application readers change their PREDICT behavior, data schemas, or export
  signatures.
- The repository adds a user-facing backend or a safe script that this graph
  does not cover.

The generated runtime content contains distilled guidance and bounded helpers;
it remains usable after the evidence checkout is removed.
