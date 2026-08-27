# Repo Provenance

schema: `disco.repo-provenance.v1`

## Source Snapshot

- Skill id: `anomalib`
- Project name in package metadata: `anomalib`
- Public project name: anomalib
- Package version: `2.6.0`
- Source commit: `5318849bbec068e2ae9b74768cba04abf5e71a9a`
- Branch: `main`
- Exact tag: none
- Remote URL: omitted-private-or-unknown
- Working tree state at generation: dirty checkout with untracked DisCo skill outputs under `skills/`
- Generated skill tree: `skills/disco/anomalib`

## Evidence Paths

Runtime skill content was derived from these relative paths:

- `README.md`
- `pyproject.toml`
- `src/anomalib/`
- `docs/source/markdown/get_started/anomalib.md`
- `docs/source/markdown/guides/how_to/`
- `docs/source/markdown/guides/reference/`
- `examples/api/`
- `examples/cli/`
- `tools/`
- `tests/`
- `skills/tests/anomalib/reports/integration/`

## Installed Package Facts Verified During Generation

- `anomalib` imported successfully in the private inspection environment.
- `anomalib.__version__` reported `2.6.0`.
- Public constructors and helpers were inspected for the data, model, engine, deploy, and pipeline surfaces.
- CLI help, install options, and runtime package extras were verified from the installed build.
- CPU and OpenVINO support packages were available in the verified inspection environment.

## Refresh Guidance

Refresh this skill when any of the following change:

- package version, dependencies, console scripts, or optional extras;
- data module layouts, model constructors, registry behavior, or feature-extraction defaults;
- training, evaluation, callback, logging, preprocessing, or post-processing behavior;
- export formats, inferencer signatures, trust gates, or OpenVINO quantization rules;
- benchmark pipeline config shapes, tiled ensemble behavior, or CLI help semantics;
- docs, examples, tests, or repo-owned tools that underpin these workflows.
