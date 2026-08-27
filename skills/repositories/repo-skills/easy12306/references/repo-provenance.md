# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an easy12306 checkout. If the current repo commit, dirty state, package/dependency surface, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T07:11:47Z",
  "repository": {
    "name": "easy12306",
    "remote_url": "https://github.com/zhaipro/easy12306.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "1d47934f2aa5a788f470ee30265a71064cdd3ab7",
    "working_tree": "dirty-generated-artifacts",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": [
        "main",
        "mlearn",
        "mlearn_for_image",
        "pretreatment",
        "verify_image_hash",
        "category_images"
      ],
      "notes": "The repository is a flat script collection with no installable Python distribution metadata. baidu.py was inspected statically only because it performs an import-time network token request."
    }
  ],
  "dependency_baseline": {
    "python": "3.11",
    "tensorflow_cpu": "2.15.1",
    "keras": "2.15.0",
    "opencv_python_headless": "4.11.0.86",
    "numpy": "1.26.4",
    "scipy": "1.17.1",
    "scikit_learn": "1.9.0",
    "matplotlib": "3.11.1",
    "requests": "2.34.2"
  },
  "evidence": {
    "source_roots": [
      "main.py",
      "mlearn.py",
      "mlearn_for_image.py",
      "pretreatment.py",
      "verify_image_hash.py",
      "category_images.py",
      "baidu.py"
    ],
    "docs": [
      "README.md"
    ],
    "metadata": [
      "requirements.txt",
      ".gitignore",
      "LICENSE"
    ],
    "data_reference": [
      "texts.txt"
    ],
    "examples": [],
    "tests": [],
    "configs": []
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If source files, dependency files, `README.md`, or `texts.txt` change, run `refresh-repo-skill` even if the commit is the same.
- Ignore changes only under generated skill/review paths when evaluating source staleness.
- If a future checkout adds package metadata, CLI entry points, tests, examples, or bundled model/data artifacts, refresh this skill because routing and verification assumptions may change.
