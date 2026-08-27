# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public APIs, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-13T17:20:15Z",
  "repository": {
    "name": "ImageAI",
    "remote_url": "https://github.com/OlafenwaMoses/ImageAI.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "2156d1a39a196c72057771d1d16226388c1d7baf",
    "working_tree": "dirty-generated-skill-output-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "imageai",
      "version": "3.0.3",
      "import_names": ["imageai"]
    }
  ],
  "evidence": {
    "source_roots": [
      "imageai/"
    ],
    "docs": [
      "README.md",
      "BACKEND_MIGRATION.md",
      "imageai/Classification/README.md",
      "imageai/Classification/CUSTOMCLASSIFICATION.md",
      "imageai/Classification/CUSTOMTRAINING.md",
      "imageai/Detection/README.md",
      "imageai/Detection/VIDEO.md",
      "imageai/Detection/Custom/CUSTOMDETECTION.md",
      "imageai/Detection/Custom/CUSTOMDETECTIONTRAINING.md",
      "imageai/Detection/Custom/CUSTOMVIDEODETECTION.md"
    ],
    "examples": [
      "examples/"
    ],
    "tests": [
      "test/"
    ],
    "scripts": [
      "scripts/pascal_voc_to_yolo.py"
    ],
    "excluded_or_reference_only": [
      "imageai_tf_deprecated/",
      ".github/",
      "large release model/data downloads"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale and run `refresh-repo-skill`.
- If ImageAI package metadata or public class/method signatures changed, refresh even on the same commit.
- If a checkout's current working tree has source changes outside generated skill/artifact paths, refresh before relying on API or troubleshooting details.
- If the active ImageAI major backend changes again, refresh the install/model-asset and legacy TensorFlow guidance.
