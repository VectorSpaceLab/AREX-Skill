# Datamol Cross-Cutting Troubleshooting

Read this when a datamol task fails before it clearly belongs to one sub-skill, or when an error spans parsing, RDKit, optional dependencies, data files, and downstream workflows.

## Install And Import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ImportError: No module named datamol` | Datamol is not installed in the active Python environment. | Install with `mamba install -c conda-forge datamol` or `python -m pip install datamol`, then run `python -c "import datamol as dm; print(dm.__version__)"`. |
| RDKit import errors or ABI/library errors | RDKit wheel/conda package is missing or incompatible with Python/platform. | Prefer conda-forge for RDKit-heavy environments. Recreate the environment with a Python version supported by datamol and RDKit instead of mixing incompatible packages. |
| Public package imports but a specific helper is missing | The installed datamol version differs from the skill provenance snapshot. | Check `references/repo-provenance.md`; if API names or package metadata differ, refresh the skill. |
| Current checkout editable install fails around dynamic versioning | Local build metadata cannot infer a version from the checkout. | For development installs, use a valid public tag/metadata state or a build-system-supported version override. Do not publish private override values as package versions. |

## RDKit Molecule Parsing And Sanitization

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `dm.to_mol(...)` returns `None` | Invalid SMILES/SMARTS-like input, strict parser settings, or sanitization failure. | Use `molecule-io-prep` troubleshooting. Try `sanitize=False` only for inspection, then explicitly sanitize/standardize before downstream workflows. |
| RDKit prints warnings during parsing or conformer generation | RDKit reports chemistry edge cases even when datamol returns usable molecules. | Capture warnings in review logs when useful. For noisy probes, use `visualization-utilities` log-control guidance. |
| Downstream fingerprints, reactions, or drawings fail after IO | Inputs were not cleaned, properties were lost, or invalid rows were kept unexpectedly. | Route back to `molecule-io-prep`; preserve identifiers, choose `discard_invalid` behavior, and validate molecule counts before moving on. |

## Optional Dependencies And File Formats

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Excel/parquet/remote path read fails | Optional pandas engine, filesystem implementation, or credentials are missing. | Validate local CSV/SDF first. Install the relevant pandas/fsspec backend only when the workflow needs it. Do not assume cloud credentials exist. |
| Image output fails in headless or notebook-free environments | Raster/image/widget stack is missing or a notebook-only display path was used. | Prefer SVG output from `visualization-utilities`; install optional notebook widgets only when interactive 3D display is required. |
| `networkx` errors when using graph helpers | Graph helper dependencies are missing in a minimal install. | Install the missing dependency or avoid graph-specific workflows; use `fingerprints-similarity` for graph helper guidance. |

## Performance And Combinatorial Growth

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Conformer, isomer, fragment, reaction, fuzzy scaffold, or MCS workflow runs too long | Chemistry search space is combinatorial or defaults were too broad. | Start with small `n_confs`, `n_variants`, `timeout`, `timeout_seconds`, `depth`, `max_n_mols`, `num_threads=1`, and `n_jobs=1`; increase only after validating behavior. |
| Parallel job fails with pickling or hidden exceptions | Callable is not picklable, process scheduler hides the original error, or shared state is unsafe. | Use `visualization-utilities` utility troubleshooting; try `scheduler="threads"`, `n_jobs=1`, and top-level functions. |
| Distance matrix or descriptor workflow is memory-heavy | All-vs-all matrices scale quadratically or descriptors were computed on too many molecules. | Use `fingerprints-similarity` chunking and `distances_chunk` guidance; start with a representative subset. |

## Routing Recovery

- If a task starts from files or strings and fails later, return to `sub-skills/molecule-io-prep/` and validate molecule counts, canonical SMILES, and properties first.
- If a numeric workflow fails after molecules are valid, go to `sub-skills/fingerprints-similarity/` for fingerprint type, shape, clustering, MCS, or graph guidance.
- If a generated chemistry workflow fails or grows too large, go to `sub-skills/structure-generation/` for bounds, timeouts, and reaction/enumeration recovery.
- If output artifacts or helper utilities fail, go to `sub-skills/visualization-utilities/` for rendering, fsspec, RDKit logging, and parallel utility recovery.
