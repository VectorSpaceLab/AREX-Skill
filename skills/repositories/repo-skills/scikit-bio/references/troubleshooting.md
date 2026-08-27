# Cross-Cutting Troubleshooting

Read this when a scikit-bio task fails before it reaches a specific sub-skill, when installation/imports fail, or when object IDs do not line up across sequence, tree, table, metadata, diversity, and statistics workflows.

## Install or Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'skbio'`.
- Import fails for `numpy`, `pandas`, `scipy`, `h5py`, `biom`, `statsmodels`, or `patsy`.
- Editable installs or local builds fail while compiling Cython extensions.

Checks and fixes:

1. Confirm Python is supported: scikit-bio requires Python 3.10 or newer.
2. Prefer `conda install -c conda-forge scikit-bio` when compiled wheels or system libraries are difficult to resolve.
3. If using pip, run `python -m pip check` after install to catch incompatible dependency versions.
4. Run `python scripts/check_skbio_environment.py` from this skill directory, or address the script by path from any working directory.
5. If a repository checkout is being tested, install with test dependencies only when focused native pytest verification is needed; do not install broad docs/lint/dev extras for ordinary API use.

## No CLI or Entry Point Exists

Symptoms:

- A task asks for a `skbio` shell command or command-line flags.
- Package metadata has no console script entry points.

Checks and fixes:

- Treat scikit-bio as a Python library. Write a short Python snippet or use the bundled smoke scripts instead of inventing a CLI.
- For file conversion, use `skbio.io.read` and `skbio.io.write` from Python.
- For repository verification, run focused `pytest` modules only after a generated skill is integrated and native candidates are classified as safe.

## ID Alignment Problems

Symptoms:

- Diversity metrics reject taxa or sample IDs.
- PERMANOVA/ANOSIM grouping does not match a `DistanceMatrix`.
- Metadata filtering silently removes expected samples.
- UniFrac or Faith PD reports missing tree tips or branch lengths.

Checks and fixes:

1. Normalize sample IDs, feature/taxon IDs, tree tip names, metadata index values, and distance-matrix IDs before analysis.
2. Keep count matrices oriented as rows = samples and columns = taxa/features for diversity drivers.
3. Preserve `DistanceMatrix.ids` when creating metadata groupings or ordination inputs.
4. Validate tree tip names and branch lengths in `sub-skills/trees-phylogeny/SKILL.md` before running phylogenetic diversity in `sub-skills/diversity-tables/SKILL.md`.
5. Use explicit metadata column names when calling statistics functions that accept a DataFrame plus `column=`.

## Validation vs Performance

Symptoms:

- A slow workflow tempts `validate=False`.
- An invalid input produces confusing downstream NumPy/SciPy errors.

Checks and fixes:

- Keep validation enabled while developing or debugging.
- Disable validation only after checking counts are non-negative integers, matrices are symmetric/hollow where required, tree tip names are unique, metadata IDs align, and table axes are correct.
- Record why validation is safe to disable in any generated analysis script.

## Optional Array and GPU Backends

Symptoms:

- Array API inputs behave differently from NumPy arrays.
- GPU-resident arrays fail or return unsupported-output errors.

Checks and fixes:

- Start with NumPy/pandas inputs unless the task explicitly needs an alternate array backend.
- Composition functions may support array API inputs, but not every downstream workflow preserves GPU arrays or non-NumPy containers.
- Route backend-specific compositional or ordination questions to `sub-skills/statistics-ordination/SKILL.md`.

## Where to Go Next

- File format, metadata, and registry problems: `sub-skills/io-metadata/SKILL.md`.
- Sequence, translation, MSA, or alignment problems: `sub-skills/sequences-alignment/SKILL.md`.
- Tree parsing, branch lengths, rooting, or tip-name problems: `sub-skills/trees-phylogeny/SKILL.md`.
- Count matrices, diversity metrics, UniFrac, and `Table` orientation problems: `sub-skills/diversity-tables/SKILL.md`.
- Distance-matrix tests, ordination, compositional data, and embeddings: `sub-skills/statistics-ordination/SKILL.md`.
