# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of pySCENIC. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-24T00:00:00Z",
  "repository": {
    "name": "pySCENIC",
    "remote_url": "https://github.com/aertslab/pySCENIC",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "06bafba412792f6efa5a552a23bb221cc3bdea1b",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "pyscenic",
      "version": "0+untagged.1.g06bafba",
      "import_names": [
        "pyscenic"
      ]
    }
  ],
  "evidence": {
    "source_roots": [
      "src/pyscenic",
      "src/resources"
    ],
    "docs": [
      "README.rst",
      "docs/installation.rst",
      "docs/tutorial.rst",
      "docs/faq.rst",
      "docs/releasenotes.rst"
    ],
    "examples": [
      "notebooks"
    ],
    "scripts": [
      "scripts/cli_test_script.sh",
      "scripts/hpc-grnboost.py",
      "scripts/hpc-grnboost.ini",
      "scripts/hpc-prune.py",
      "scripts/hpc-prune.ini",
      "src/pyscenic/cli/arboreto_with_multiprocessing.py",
      "src/pyscenic/cli/csv2loom.py"
    ],
    "tests": [
      "tests/test_aucell.py",
      "tests/test_featureseq.py",
      "tests/test_math.py"
    ],
    "configs": [
      "setup.py",
      "setup.cfg",
      "requirements.txt",
      "requirements_docker_with_scanpy.txt",
      "tox.ini",
      "Dockerfile",
      "pyscenic_with_scanpy.Dockerfile"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ from `repository.dirty_paths`, run `refresh-repo-skill` before relying on this skill for changed behavior.
- If pySCENIC package metadata, public entry points, CLI flags, source APIs, docs, examples, or supported file formats changed, run `refresh-repo-skill`.
- The snapshot records only relative evidence paths and public package facts; private Python environments and local installation paths are intentionally omitted.
