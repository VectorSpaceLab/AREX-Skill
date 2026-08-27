# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of `cysmith/neural-style-tf`. If the current repository commit, dirty state, public script surface, or evidence paths differ from this snapshot, run `refresh-repo-skill` before relying on the skill for new work.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T06:49:27Z",
  "repository": {
    "name": "neural-style-tf",
    "remote_url": "https://github.com/cysmith/neural-style-tf.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "a2c374f9ee2938f0022e1e0b720f4eb28cf7d0a8",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [],
      "notes": "The repository is a script-style application centered on neural_style.py; no pyproject.toml, setup.py, setup.cfg, requirements file, or installable distribution metadata was present."
    }
  ],
  "evidence": {
    "source_roots": ["neural_style.py"],
    "docs": ["README.md"],
    "examples": ["examples/", "image_input/", "styles/", "video_input/"],
    "tests": [],
    "scripts": ["stylize_image.sh", "stylize_video.sh", "video_input/make-opt-flow.sh", "video_input/run-deepflow.sh"],
    "generated_or_review_artifacts_excluded": ["skills/"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale and run `refresh-repo-skill`.
- If `neural_style.py` changes parser flags, defaults, TensorFlow API usage, output layout, image/video helper functions, or video temporal logic, refresh before using the CLI references.
- If the README setup/usage sections, shell wrappers, or `video_input` helper scripts change, refresh the affected sub-skills and source-script import map.
- The dirty path recorded here was the production `skills/` area, not a source-code change. If a future checkout has dirty source files such as `neural_style.py` or shell helpers, refresh or inspect those changes directly.
