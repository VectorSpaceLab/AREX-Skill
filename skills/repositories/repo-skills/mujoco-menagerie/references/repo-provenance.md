# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of MuJoCo Menagerie. If the current repo commit, dirty state, model catalog, scripts, tests, or public evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:59:17Z",
  "repository": {
    "name": "mujoco_menagerie",
    "remote_url": "https://github.com/google-deepmind/mujoco_menagerie.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "da76818e269b82289eba39808e2fb91d679d6994",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": null,
      "version": null,
      "import_names": []
    },
    {
      "name": "mujoco",
      "version": "3.11.0",
      "import_names": ["mujoco"]
    }
  ],
  "evidence": {
    "source_roots": [
      "68 top-level model directories containing MJCF XML and assets"
    ],
    "docs": [
      "README.md",
      "FAQ.md",
      "CONTRIBUTING.md",
      "CHANGELOG.md",
      "CITATION.cff",
      "per-model README.md files"
    ],
    "examples": [],
    "tests": [
      "test/model_test.py",
      "test/model_dir_test.py",
      "test/requirements.txt"
    ],
    "configs": [
      "pyproject.toml",
      ".pre-commit-config.yaml",
      ".github/workflows/build.yml",
      "Makefile"
    ],
    "scripts": [
      "format_xml.py",
      "regenerate_license.py",
      "generate_gallery.py",
      "flexiv_rizon4/compute_gains.py",
      "trossen_wxai/create_biarm.py",
      "sharpa_wave/make_right.py"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from the recorded commit, treat this skill as potentially stale.
- If the current checkout has model directories, XML variant names, `generate_gallery.py` `MODEL_MAP` entries, validation tests, or maintainer scripts that differ from the snapshot evidence, refresh the skill.
- If the working tree is dirty for source files outside generated skill artifacts, refresh before relying on catalog or maintainer guidance.
- Because Menagerie is an XML/model asset repository rather than a Python distribution, package-version drift is mainly about the installed `mujoco` binding and the XML features required by individual model READMEs.
