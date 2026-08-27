# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of SketchCode. If the current repo commit, dirty state, package/runtime layout, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-15T17:12:14Z",
  "repository": {
    "name": "sketch-code",
    "remote_url": "https://github.com/ashnkumar/sketch-code.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "0be7c3b5d1cd0b361b92746ce4d2530cd2de0d0e",
    "working_tree": "clean-before-skill-generation",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": ["classes"]
    }
  ],
  "runtime_dependencies": {
    "documented_requirements": [
      "Keras==2.1.2",
      "tensorflow==1.4.0",
      "nltk==3.2.5",
      "opencv-python==3.3.0.10",
      "numpy==1.13.1",
      "h5py==2.7.1",
      "matplotlib==2.0.2",
      "Pillow==4.3.0",
      "tqdm==4.17.1",
      "scipy==1.0.0"
    ],
    "inspection_note": "The repository has no pyproject.toml/setup.py/setup.cfg; source import root is src/classes. The exact OpenCV 3.3.0.10 wheel was unavailable during inspection, so a nearby OpenCV 3.x wheel was used only to verify preprocessing behavior."
  },
  "evidence": {
    "source_roots": ["src", "src/classes"],
    "docs": ["README.md", "README_kr.md", "Document_kr.md"],
    "examples": ["examples"],
    "scripts": ["scripts/get_data.sh", "scripts/get_pretrained_model.sh"],
    "tests": [],
    "configs_or_assets": ["requirements.txt", "vocabulary.vocab", "src/classes/inference/styles"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat this skill as potentially stale and run `refresh-repo-skill`.
- If package metadata appears in a future checkout, or the public runtime stops using `src/classes`, refresh this skill.
- If conversion/training/evaluation scripts or style mapping files change, refresh the corresponding sub-skill.
- If dependency pins, asset URLs, model file names, or vocabulary tokens change, refresh the root environment/assets reference and affected sub-skills.
