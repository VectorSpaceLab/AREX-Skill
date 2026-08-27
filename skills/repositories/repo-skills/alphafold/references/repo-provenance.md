# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an AlphaFold checkout. If the current repo commit, dirty state, package version, public entry points, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-29T00:00:00Z",
  "repository": {
    "name": "alphafold",
    "remote_url": "https://github.com/google-deepmind/alphafold.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "c77e5d2a8961d1a353632c462914ff0a32a950f6",
    "working_tree": "dirty-generated-skill-artifacts-only",
    "dirty_paths": [
      "skills/"
    ]
  },
  "packages": [
    {
      "name": "alphafold",
      "version": "2.3.2",
      "import_names": ["alphafold", "run_alphafold"]
    }
  ],
  "evidence": {
    "metadata": ["pyproject.toml", "requirements.txt", "docker/requirements.txt"],
    "source_roots": ["alphafold/common", "alphafold/data", "alphafold/model", "alphafold/notebooks", "alphafold/relax", "run_alphafold.py", "docker/run_docker.py"],
    "docs": ["README.md", "docs/technical_note_v2.3.0.md", "afdb/README.md", "server/README.md"],
    "examples": ["server/example.json", "notebooks/AlphaFold.ipynb"],
    "scripts": ["scripts/download_all_data.sh", "scripts/download_alphafold_params.sh", "scripts/download_bfd.sh", "scripts/download_mgnify.sh", "scripts/download_pdb70.sh", "scripts/download_pdb_mmcif.sh", "scripts/download_pdb_seqres.sh", "scripts/download_small_bfd.sh", "scripts/download_uniprot.sh", "scripts/download_uniref30.sh", "scripts/download_uniref90.sh"],
    "tests": ["run_alphafold_test.py", "alphafold/common/*_test.py", "alphafold/data/*", "alphafold/model/*_test.py", "alphafold/notebooks/notebook_utils_test.py", "alphafold/relax/*_test.py"]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If package metadata, dependency pins, console entry points, model presets, database path conventions, output file names, or public APIs changed, run `refresh-repo-skill` even on the same commit.
- If the checkout's dirty paths include source, docs, examples, tests, scripts, Docker files, or package metadata beyond generated skill artifacts, run `refresh-repo-skill` before trusting the skill.
- If the current package version differs from `2.3.2`, verify whether the model presets, data layout, and dependency pins still match before using this skill for commands.
