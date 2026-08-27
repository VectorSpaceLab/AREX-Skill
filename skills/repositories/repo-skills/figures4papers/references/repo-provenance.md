# Repository Provenance

## Purpose

Read this before deciding whether the `figures4papers` repo skill is current for a checkout. If the current commit, dirty state, dependency surface, or major evidence paths differ from this snapshot, refresh the skill before relying on it for repository-specific guidance.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T07:05:54Z",
  "repository": {
    "name": "figures4papers",
    "remote_url": "https://github.com/ChenLiu-1996/figures4papers.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "6790a93af3552539d955d77181c818916e1700b7",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [],
  "runtime_dependencies_observed": [
    {"name": "numpy", "version": "2.4.6", "import_names": ["numpy"]},
    {"name": "matplotlib", "version": "3.11.1", "import_names": ["matplotlib"]},
    {"name": "scipy", "version": "1.17.1", "import_names": ["scipy"]},
    {"name": "seaborn", "version": "0.13.2", "import_names": ["seaborn"]},
    {"name": "python-dateutil", "version": "2.9.0.post0", "import_names": ["dateutil"]}
  ],
  "repository_shape": {
    "installable_python_package": false,
    "public_cli_entry_points": [],
    "public_import_roots": [],
    "optional_system_dependencies": ["LaTeX for exact text.usetex=True reproduction"]
  },
  "evidence": {
    "docs": [
      "README.md",
      "scientific-figure-making/SKILL.md",
      "scientific-figure-making/references/api.md",
      "scientific-figure-making/references/common-patterns.md",
      "scientific-figure-making/references/design-theory.md",
      "scientific-figure-making/references/tutorials.md",
      "scientific-figure-making/references/demos.md"
    ],
    "examples_and_scripts": [
      "figure_Brainteaser/*.py",
      "figure_CellSpliceNet/*.py",
      "figure_Cflows/*.py",
      "figure_Dispersion/*.py",
      "figure_ImmunoStruct/*.py",
      "figure_RNAGenScape/*.py",
      "figure_VIGIL/*.py",
      "figure_ophthal_review/*.py"
    ],
    "visual_outputs": [
      "figure_*/figures/*",
      "assets/*.png"
    ],
    "tests": [],
    "configs": [".gitignore"]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale and run `refresh-repo-skill`.
- If the checkout has new or changed figure directories, plotting scripts, generated-skill files, or existing repo-local skill guidance, refresh before relying on route coverage.
- If the repository becomes an installable Python package, gains shared helper modules, or adds public CLIs, refresh so API/CLI guidance can be verified from package metadata.
- If optional dependencies change, especially TeX, seaborn, SciPy, or matplotlib version behavior, re-run the environment check and refresh troubleshooting notes as needed.

## Evidence notes

This skill distills reusable plotting patterns and bundled templates from the repository scripts. The runtime skill does not require the original checkout, source scripts, generated figures, or local environment paths to be present.
