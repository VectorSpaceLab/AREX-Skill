# Visualization and Utility Troubleshooting

Use this guide when rendering, highlighting, filesystem, logging, or parallel utility tasks fail.

## Rendering and Image Output

| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| SVG output is an IPython object instead of a string | Code is running inside a notebook/IPython display context. | Write with `outfile` or use the object's display data. For deterministic scripts, run outside notebooks. |
| PNG output is an IPython image object instead of `PIL.Image.Image` | Notebook/IPython context changes RDKit/datamol return types. | Prefer `outfile="image.png"` for portable scripts, or run in a plain Python process. |
| `PIL.UnidentifiedImageError` when opening PNG | File was written as SVG or incomplete bytes, or `use_svg` did not match extension. | Use `use_svg=False` for PNG and `use_svg=True` for SVG; verify the file extension and write path. |
| Empty or huge grid artifact | Input list is empty or too large. | Validate molecule list length, set `max_mols`, and choose a smaller `mol_size`/`n_cols`. |
| Kekulization/aromaticity drawing error | Unusual aromatic/query molecule preparation failed. | Try `kekulize=False`; if parsing or sanitization is the root issue, route to `../molecule-io-prep/`. |
| Molecules are not visually aligned | 2D orientation differs across molecules. | Use `align=True` for automatic 2D alignment or `align=<template_mol>` for template alignment. Route advanced alignment to `../structure-generation/`. |
| Headless environment display fails | Code assumes notebook GUI display or browser-backed rendering. | Save SVG/PNG to a file with `outfile`; avoid `dm.viz.conformers()` unless notebook widget dependencies and frontend display are available. |

## Lasso and Substructure Highlighting

| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| `ValueError: Please enter a valid target molecule or smiles` | Target is `None`, empty, or cannot be parsed. | Validate target SMILES/molecule first with `dm.to_mol()`; route cleanup to `../molecule-io-prep/`. |
| `ValueError: Please enter valid search molecules or smarts` | SMARTS/query is invalid or conversion returned `None`. | Validate each query with `dm.from_smarts()` or pass a valid RDKit query molecule. |
| No visible lasso highlight | Query has no substructure match; an empty query list was used; atom indices do not correspond to the target. | Draw atom indices with `dm.viz.to_image(..., indices=True)`, confirm `mol.GetSubstructMatches(query)`, or provide correct `atom_indices`. |
| `bondLineWidthXXXX` or custom option error | Unknown RDKit draw option was passed through `**kwargs`. | Use RDKit `MolDrawOptions` names exactly, such as `bondLineWidth`, or remove the option. |
| Colors look wrong | Mixed 0-255 and 0-1 color tuples or malformed hex strings. | Use valid hex strings such as `"#ff1472"` or RGB/RGBA tuples consistently. |
| Multiple regions reuse colors | Fewer colors than matched regions. | Provide a longer `color_list`; datamol cycles colors when the list is short. |
| `highlight_atoms`/`highlight_bonds` has wrong shape | RDKit drawer expects a list per molecule for multi-molecule grids. | For multiple targets, pass `[[atom_ids_for_mol1], [atom_ids_for_mol2]]` and matching color dictionaries per molecule. |

## DataFrame and Notebook Display

| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| `dm.render_mol_df(df)` returns `None` | The function mutates DataFrame display formatting in-place. | Call it for notebook display side effects; do not assign the return value. |
| DataFrame molecule column is missing or plain strings | DataFrame was not built with molecules or rendering disabled. | Use `dm.to_df(mols, mol_column="mol", render_df_mol=True)` or route table conversion to `../molecule-io-prep/`. |
| Notebook-only visualization code fails in scripts | Display formatters/widgets are notebook features. | Use file output with `to_image(..., outfile=...)` for script workflows. |

## 3D Conformer Visualization

| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| `ImportError` mentions `nglview` | Optional 3D notebook dependency is missing. | Install/configure `nglview` only if the user needs interactive 3D notebooks; otherwise use 2D rendering. |
| `ImportError` mentions `ipywidgets` | Optional notebook widgets are missing. | Install/configure notebook widgets or avoid `dm.viz.conformers()`. |
| `ValueError` says molecule has 0 conformers | 3D coordinates were not generated. | Use `../structure-generation/` to generate conformers with `dm.conformers.generate()` before visualization. |
| Conformer grid is slow or cluttered | Too many conformers or large molecule. | Limit `n_confs`, set `n_cols`, or render selected conformers only. |

## fsspec and Filesystem Helpers

| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| Remote URI fails in `outfile`, `copy_file`, or `glob` | Required fsspec backend or credentials are not installed/configured. | Confirm `dm.utils.fs.get_protocol(path)`, install/configure the backend outside the skill, and avoid embedding credentials. |
| `copy_file` raises destination exists | `force=False` by default. | Use a new path or pass `force=True` only when overwriting is intended. |
| `copy_file` raises source missing/not a file | Source path is wrong or points to a directory. | Check `dm.utils.fs.is_file(source)` and `dm.utils.fs.is_dir(source)` before copying. |
| `mkdir` raises for existing directory | `exist_ok=False` by default. | Pass `exist_ok=True` when idempotent directory creation is intended. |
| `join` creates unexpected separators | The first path controls the filesystem separator. | Put the URI/root path first, then relative path components. |
| `glob` returns unexpected protocol formatting | fsspec backend differences. | Use `dm.utils.fs.get_protocol()` and inspect returned paths before downstream parsing. |

## Parallel Jobs and JobRunner

| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| Joblib pickling error | Process workers cannot pickle lambdas, closures, notebook functions, or complex objects. | Define a top-level function, use `scheduler="threads"`, or set `n_jobs=1` for sequential execution. |
| Function receives wrong argument shape | `arg_type` does not match input items. | Use `arg_type="arg"` for single inputs, `"args"` for tuples/lists, and `"kwargs"` for dictionaries. |
| Progress bar total is wrong for a generator | Length cannot be inferred. | Pass `total=<expected_count>` when `progress=True`. |
| Parallel execution is slower than sequential | Inputs are tiny or overhead dominates. | Use `n_jobs=1` or batch with `parallelized_with_batches()`. |
| Exceptions are hard to read from workers | Process backend wraps worker exceptions. | Reproduce with `n_jobs=1`, then re-enable threads/processes after fixing the callable. |
| Thread/process choice is unclear | CPU-bound picklable work may benefit from processes; IO-bound or notebook work is safer with threads. | Start with `n_jobs=1` for correctness, then `scheduler="threads"` for robustness, then processes only when pickling is safe. |

## RDKit Logs and Version Gates

| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| SMILES parse warnings clutter output | RDKit logs are enabled during expected invalid-input probes. | Use `with dm.without_rdkit_log():` around the probe or decorate a helper with `@dm.no_rdkit_log()`. |
| Logs stay muted after a task | Global `dm.disable_rdkit_log()` was used without restoration. | Prefer the context manager. If global muting was necessary, call `dm.enable_rdkit_log()` in a `finally` block. |
| API behavior differs across RDKit releases | Drawing or helper implementation is version-sensitive. | Gate behavior with datamol helpers such as `dm.is_greater_eq_than_current_rdkit_version("2023.03")`. |
| Debugging hides real parse failures | Overbroad log muting suppresses useful RDKit errors. | Temporarily set `enable=False` in `without_rdkit_log()` or re-enable logs for the failing case. |

## Diagnostic Checklist

1. Confirm `import datamol as dm` succeeds in the user's runtime.
2. Render `dm.viz.to_image("CCO", use_svg=True)` before trying complex molecules.
3. Write to a local `outfile` before trying remote fsspec URIs.
4. For highlights, render atom/bond indices before passing explicit index lists.
5. Reproduce parallel failures with `n_jobs=1`; switch to `scheduler="threads"` before trying processes again.
6. For 3D display, confirm conformers exist and optional notebook dependencies are installed.
