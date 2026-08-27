# Repository Provenance

## Purpose

Read this before deciding whether this skill still matches the current Mars
checkout. If the commit, dirty state, package version, or evidence paths differ,
run a refresh workflow instead of assuming this skill is current.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T12:15:54Z",
  "repository": {
    "name": "mars",
    "remote_url": "https://github.com/mars-project/mars.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "bcc000554c8bd9ebd5cafe7c61b1f0090ab9d53b",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "pymars",
      "version": "0+untagged.1.gbcc0005",
      "import_names": ["mars"]
    }
  ],
  "evidence": {
    "source_roots": ["mars"],
    "docs": ["README.rst", "docs/source"],
    "examples": [
      "mars/remote/tests/sample_script.py",
      "mars/learn/contrib/pytorch/tests/pytorch_sample.py",
      "mars/learn/contrib/tensorflow/tests/tf_distributed_sample.py"
    ],
    "tests": ["mars/**/tests"],
    "configs": ["pyproject.toml", "setup.cfg", "setup.py", "conda-spec.txt"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, refresh the skill.
- If the dirty paths change materially, refresh the skill.
- If public entry points or package metadata change, refresh the skill.
- If optional backend guidance changes because dependencies or docs moved,
  refresh the affected sub-skill first and then the root.
