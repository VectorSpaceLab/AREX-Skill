# MDAnalysis Repo Provenance

Schema: `disco.repo-provenance.v1`

This skill was generated from repository evidence for the MDAnalysis source tree.

## Source Snapshot

- Source repository: MDAnalysis/mdanalysis
- Remote URL: https://github.com/MDAnalysis/mdanalysis
- Branch: `develop`
- Commit: `d25f074b7d9a24fbcd5ee9c6c9bd9751001949b7`
- Exact tag: none detected
- Working tree state at generation: dirty because the generated `skills/` output was added during this run
- Package distribution: `MDAnalysis`
- Package/import version observed during inspection: `2.11.0.dev0` / `2.11.0-dev0`
- Python support from package metadata: `>=3.11`

## Evidence Paths

- `README.rst`
- `package/README`
- `package/pyproject.toml`
- `package/setup.py`
- `package/setup.cfg`
- `package/requirements.txt`
- `package/MDAnalysis/`
- `package/doc/sphinx/source/documentation_pages/`
- `testsuite/MDAnalysisTests/`
- `testsuite/scripts/modeller_make_A6PA6_alpha.py`
- `benchmarks/benchmarks/` as evidence only

## Generated Coverage Baseline

The generated skill covers public MDAnalysis usage workflows:

- Universe construction, loading, trajectory iteration, and basic writing
- Atom selections, topology attributes, groups, fragments, and selection exporters
- Built-in analysis modules and custom `AnalysisBase` workflows
- On-the-fly transformations and transformed output writing
- Format support, optional dependencies, converters, auxiliary data, and fetcher troubleshooting

The generated skill intentionally excludes maintainer release/CI infrastructure, benchmark execution, and exhaustive deep coverage of every analysis module or every file format implementation detail.

## Refresh Triggers

Refresh this skill when MDAnalysis changes any of these surfaces:

- `Universe`, `AtomGroup.select_atoms`, `AnalysisBase.run`, writer, transformation, converter, or optional dependency signatures
- supported Python versions or package optional-dependency groups
- supported coordinate/topology formats, fetcher behavior, or converter APIs
- selection language semantics, topology attribute behavior, or sorting/updating rules
- result container names or deprecation status for major analysis modules
