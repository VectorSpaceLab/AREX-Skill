# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for an OpenFF Toolkit checkout. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "evidence": {
    "configs": [
      "pyproject.toml",
      "MANIFEST.in",
      "devtools/conda-envs/test_env.yaml",
      "docs/environment.yml"
    ],
    "docs": [
      "README.md",
      "docs/installation.md",
      "docs/users/concepts.md",
      "docs/users/molecule_conversion.md",
      "docs/users/smirnoff.md",
      "docs/users/virtualsites.md",
      "docs/users/pdb_cookbook/index.ipynb",
      "docs/api/toolkits.md",
      "docs/topology.md",
      "docs/typing.rst"
    ],
    "examples": [
      "examples/conformer_energies/conformer_energies.py",
      "examples/forcefield_modification/",
      "examples/inspect_assigned_parameters/",
      "examples/using_smirnoff_in_amber_or_gromacs/",
      "examples/using_smirnoff_with_amber_protein_forcefield/",
      "examples/visualization/"
    ],
    "source_roots": [
      "openff/toolkit"
    ],
    "tests": [
      "openff/toolkit/_tests/test_molecule.py",
      "openff/toolkit/_tests/test_io.py",
      "openff/toolkit/_tests/test_topology.py",
      "openff/toolkit/_tests/test_forcefield.py",
      "openff/toolkit/_tests/test_parameters.py",
      "openff/toolkit/_tests/test_parameter_plugins.py",
      "openff/toolkit/_tests/test_toolkits.py"
    ],
    "utilities": [
      "utilities/test_plugins/custom_plugins/handler_plugins.py",
      "utilities/test_plugins/setup.py",
      "utilities/make_substructure_dict/"
    ]
  },
  "generated_at_utc": "2026-06-29T17:26:05Z",
  "packages": [
    {
      "import_names": [
        "openff.toolkit"
      ],
      "name": "openff-toolkit",
      "version": "0.0.1.dev1+g120f71473"
    }
  ],
  "repository": {
    "branch": "main",
    "commit": "120f71473a4b87cb314bd7acc706ce7e9ffdeda4",
    "dirty_paths": [
      "skills/"
    ],
    "name": "openff-toolkit",
    "remote_url": "https://github.com/openforcefield/openff-toolkit.git",
    "tag": null,
    "vcs": "git",
    "working_tree": "dirty"
  },
  "schema": "disco.repo-provenance.v1"
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-repo-skill`.
- If the current working tree dirty paths differ from `repository.dirty_paths`, run `refresh-repo-skill` or review the changes before using the skill.
- If OpenFF Toolkit public APIs, package metadata, SMIRNOFF handlers, optional backend behavior, examples, or docs change, refresh this skill even on the same commit.
