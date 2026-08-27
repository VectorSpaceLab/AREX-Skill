# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, public scripts, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T16:14:30Z",
  "repository": {
    "name": "fast-style-transfer",
    "remote_url": "https://github.com/lengstrom/fast-style-transfer.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "0d3d981f7ab948253d355585bdbdfa914247b4d0",
    "working_tree": "clean before skill artifact generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["style", "evaluate", "transform_video", "transform", "optimize", "vgg", "utils"]
    }
  ],
  "citation": {
    "title": "Fast Style Transfer",
    "version": "1.0",
    "date_released": "2016-10-31",
    "author": "Logan Engstrom"
  },
  "evidence": {
    "source_roots": ["src"],
    "top_level_scripts": ["style.py", "evaluate.py", "transform_video.py", "setup.sh"],
    "docs": ["README.md", "docs.md", "CITATION.cff"],
    "examples": ["examples/content", "examples/style", "examples/results", "examples/thumbs"],
    "tests": [],
    "configs": []
  },
  "verification_context": {
    "script_help_checked": ["style.py", "evaluate.py", "transform_video.py"],
    "safe_smokes_checked": ["transform.net tiny graph", "utils image save/load roundtrip"],
    "not_downloaded": ["VGG19 .mat", "COCO train2014", "pretrained checkpoints"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If public script flags in the bundled training runtime, the bundled image stylization runtime, or the bundled video stylization runtime changed, refresh the matching sub-skill.
- If TensorFlow compatibility requirements or asset URLs changed in public docs, refresh the setup/troubleshooting references.
- If the repository becomes a packaged distribution with metadata or entry points, refresh root install guidance and provenance package fields.
