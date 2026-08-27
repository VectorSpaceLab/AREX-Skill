# Repository provenance

## Generation baseline

This skill tree was derived from the following source state:

- Repository: `scikit-image/scikit-image`
- Source form: local Git checkout of the public repository
- Branch: `main`
- Commit: `cb1adbd63149f69e9b10be55e686b1fc457dd1a4`
- Source version: `0.26.1rc0.dev0`
- Inspected installed version: `0.26.1rc0.dev0+git20260804.cb1adbd`
- Python requirement in that source metadata: `>=3.12`
- Primary runtime namespace: `skimage`
- Experimental namespace: `skimage2`
- Hardware scope: CPU; no accelerator is required for the routed workflows

The source worktree was clean when the repository analysis was recorded. Generated skills and verification artifacts were added afterward.

## Evidence scope

The skill was distilled from the public package source, user guide, representative gallery examples and tests, package metadata, and installation guidance. The selected runtime coverage includes:

- `skimage.data`, `skimage.io`, and `skimage.util` for data and array boundaries;
- `skimage.color`, `skimage.exposure`, `skimage.filters`, and `skimage.restoration` for enhancement;
- `skimage.feature`, `skimage.measure`, and `skimage.metrics` for analysis;
- `skimage.draw`, `skimage.morphology`, `skimage.segmentation`, and `skimage.graph` for shapes and segmentation;
- `skimage.transform` and `skimage.registration` for geometry and alignment.

The `skimage2` and `_skimage2` source trees were used only to establish the experimental namespace warning and migration boundary. Maintainer-only release scripts, CI configuration, benchmarks, generated lookup tools, and broad gallery infrastructure were not converted into runtime instructions.

## Refresh triggers

Re-check or regenerate this skill when any of the following is true:

1. the active checkout is substantially newer than the commit above;
2. the installed package has a different major/minor API line;
3. `skimage2` is no longer marked experimental or its migration contract changes;
4. public functions used by a leaf have changed imports, signatures, defaults, dtype/range rules, or return structures;
5. supported Python, NumPy, SciPy, build-system, or optional-dependency requirements have changed;
6. `skimage.io` plugin behavior or sample-data download behavior has changed;
7. a routed module has been removed, renamed, or split into a new public package.

A dirty application checkout does not automatically invalidate the skill. Compare the changed public API and documentation surfaces, not just the presence of local edits.

## Staleness check

Record the live environment before trusting version-sensitive details:

```bash
python -c "import sys, skimage; print(sys.version); print(skimage.__version__); print(skimage.__file__)"
python -m pip show scikit-image
```

If source is available, also record its commit. Compare live signatures for any disputed function. The root and leaf skills intentionally emphasize workflow contracts, but experimental APIs, deprecations, dependency floors, and exact signatures can still drift.

## Independence from the source checkout

The files under `skills/disco/scikit-image/` are intended to operate without access to the original repository. Runtime guidance, route boundaries, troubleshooting, and the safe I/O smoke helper are bundled in the skill tree. Agents must not require the generation checkout to execute ordinary user workflows.
