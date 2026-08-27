# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of pix2code. If the current repo commit, dirty state, package metadata, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-11T17:03:30Z",
  "repository": {
    "name": "pix2code",
    "remote_url": "https://github.com/tonybeltramelli/pix2code.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "eab4816e397e7491b92bdcb78d9d7195afa412b3",
    "working_tree": "clean-before-generated-skill-output",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "pix2code",
      "version": null,
      "import_names": ["model", "compiler"]
    },
    {
      "name": "Keras",
      "version": "2.1.2",
      "import_names": ["keras"]
    },
    {
      "name": "tensorflow",
      "version": "1.4.0",
      "import_names": ["tensorflow"]
    },
    {
      "name": "numpy",
      "version": "1.13.3",
      "import_names": ["numpy"]
    },
    {
      "name": "opencv-python",
      "version": "3.4.0.14 used for inspection because documented 3.3.0.10 was unavailable",
      "import_names": ["cv2"]
    },
    {
      "name": "h5py",
      "version": "2.7.1",
      "import_names": ["h5py"]
    }
  ],
  "evidence": {
    "source_roots": ["model", "compiler"],
    "docs": ["README.md"],
    "examples": [],
    "tests": [],
    "configs": ["requirements.txt", "compiler/assets/android-dsl-mapping.json", "compiler/assets/ios-dsl-mapping.json", "compiler/assets/web-dsl-mapping.json"],
    "scripts": ["model/build_datasets.py", "model/convert_imgs_to_arrays.py", "model/train.py", "model/sample.py", "model/generate.py", "model/pix2code", "compiler/android-compiler.py", "compiler/ios-compiler.py", "compiler/web-compiler.py"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package pins, model constants, source script arguments, or compiler mappings change, refresh the skill.
- If a checkout adds pretrained results, tests, modern packaging, or new target platforms, refresh the sampling and DSL compilation sub-skills.
