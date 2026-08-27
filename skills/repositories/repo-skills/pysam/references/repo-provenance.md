# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-30T00:00:00Z",
  "repository": {
    "name": "pysam",
    "remote_url": "https://github.com/pysam-developers/pysam.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "30542fae25dad67e8d80e4057b6957984c3f258d",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "pysam",
      "version": "0.24.0",
      "import_names": ["pysam"]
    }
  ],
  "evidence": {
    "source_roots": ["pysam/"],
    "docs": ["README.rst", "INSTALL", "doc/usage.rst", "doc/api.rst", "doc/faq.rst", "doc/installation.rst", "doc/developer.rst"],
    "examples": [],
    "tests": ["tests/AlignmentFile_test.py", "tests/AlignedSegment_test.py", "tests/AlignmentFilePileup_test.py", "tests/VariantFile_test.py", "tests/VariantRecord_test.py", "tests/tabix_test.py", "tests/tabixproxies_test.py", "tests/faidx_test.py", "tests/samtools_test.py", "tests/test_samtools_python.py", "tests/compile_test.py", "tests/typechecking_test.py"],
    "configs": ["pyproject.toml", "setup.cfg", "setup.py", "MANIFEST.in"],
    "vendored_or_deprioritized": ["htslib/", "samtools/", "bcftools/", "devtools/", "linker_tests/"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ materially from `repository.dirty_paths`, run `refresh-repo-skill`.
- If package metadata, wrapped htslib/samtools/bcftools versions, public APIs, command wrapper inventories, or user-facing docs changed, run `refresh-repo-skill`.
- If tests or fixtures for the covered workflows changed substantially, rerun `verify-repo-skill` after refresh.
