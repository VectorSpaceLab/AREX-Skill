# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the SimpleCV repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T12:36:37Z",
  "repository": {
    "name": "SimpleCV",
    "remote_url": "https://github.com/sightmachine/SimpleCV.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "62115cc52d5d0d26373dca28d88c6c3d6bbb5260",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "SimpleCV",
      "version": "1.3.0",
      "import_names": ["SimpleCV"]
    }
  ],
  "evidence": {
    "source_roots": ["SimpleCV/"],
    "docs": ["README.md", "doc/"],
    "examples": ["SimpleCV/examples/"],
    "tests": ["SimpleCV/tests/"],
    "scripts": ["scripts/", "SimpleCV/tools/"],
    "metadata": ["setup.py", "requirements.txt"]
  }
}
```

## Evidence notes

- `setup.py` defines distribution `SimpleCV`, version `1.3`, and console script `simplecv = SimpleCV.Shell:main`.
- `SimpleCV/__init__.py` exports version `1.3.0` and imports the package's broad public API from `base`, `Camera`, `Color`, `Display`, `Features`, `ImageClass`, `Stream`, `Segmentation`, `MachineLearning`, `LineScan`, and `DFT`.
- `SimpleCV/base.py` requires an old OpenCV binding path (`cv2.cv` or `cv`) and defines optional dependency flags for PIL, freenect, ZXing, tesseract, pyscreenshot, Orange, and Vimba/pymba.
- `SimpleCV/tests/tests.py` provides native candidates for image operations, detection, segmentation, color, DFT, and line-scan behavior.
- `SimpleCV/examples/` and `SimpleCV/tools/Calibrate.py` provide workflow evidence; interactive, hardware, network, and credential-bound examples were distilled rather than copied verbatim.

## Refresh check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree is clean but this snapshot was dirty, or if dirty paths differ from `skills/` generated artifacts, inspect whether package source files changed before trusting the skill.
- If package metadata, public entry points, or OpenCV compatibility assumptions changed, refresh this skill even when the commit is unchanged.
- Do not use the generated dirty `skills/` artifacts as source evidence when refreshing; use source, docs, examples, tests, scripts, and metadata listed above.
