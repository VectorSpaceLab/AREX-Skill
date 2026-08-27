# Repository Provenance

Read this before deciding whether the skill matches a checkout. If the commit,
dirty state, package version, entry points, or major evidence paths differ,
run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-22T00:00:00Z",
  "repository": {
    "name": "ncbi-genome-download",
    "remote_url": "https://github.com/kblin/ncbi-genome-download",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "50480c7ef12b3468aaa65b1d14cc81fabdb3a5fa",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "ncbi-genome-download",
      "version": "0.3.4",
      "import_names": ["ncbi_genome_download"]
    }
  ],
  "evidence": {
    "source_roots": ["ncbi_genome_download"],
    "docs": ["README.md", "README-CN.md"],
    "examples": ["contrib/gimme_taxa.py", "ncbi-genome-download-runner.py"],
    "tests": ["tests"],
    "configs": ["setup.py", "setup.cfg", "requirements.txt", "Makefile", ".github/workflows/test.yml"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as
  potentially stale and run `refresh-repo-skill`.
- If the current dirty paths differ materially from the snapshot, refresh before
  relying on package behavior.
- Refresh if `setup.py`, console entry points, `ncbi_genome_download/config.py`,
  `core.py`, `metadata.py`, `summary.py`, or the contributed taxonomy helper
  changes.
- The snapshot was generated from a dirty checkout because the production
  workspace contains `skills/` artifacts; those artifacts are not package
  runtime evidence.
