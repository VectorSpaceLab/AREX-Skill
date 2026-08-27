# Visualization and Utility API Reference

Import datamol as `import datamol as dm`. Most visualization functions are also exported at top level, but `dm.viz.<name>` is clearer when the task is explicitly visual.

## Rendering APIs

### `dm.viz.to_image()` / `dm.to_image()`

Signature:

```python
dm.viz.to_image(
    mols, legends=None, n_cols=4, use_svg=True, mol_size=(300, 300),
    highlight_atom=None, highlight_bond=None, outfile=None, max_mols=32,
    max_mols_ipython=50, copy=True, indices=False, bond_indices=False,
    bond_line_width=2, stereo_annotations=True, legend_fontsize=16,
    kekulize=True, align=False, **kwargs,
)
```

Key behavior:

- `mols` accepts one molecule, one SMILES string, or a list of molecules/SMILES. Strings are converted through datamol molecule parsing before drawing.
- `use_svg=True` returns SVG text in a terminal process and IPython SVG objects in notebook contexts; `use_svg=False` returns a Pillow image in a terminal process and IPython image objects in notebook contexts.
- `outfile` writes the generated image through fsspec, so local paths and supported remote URI schemes use the same argument. Prefer local paths unless the user has already configured a remote filesystem.
- `mol_size` accepts an integer for square cells or `(width, height)` for grid cells.
- `highlight_atom` and `highlight_bond` may be a single list of indices for one molecule or a list per molecule.
- `align=True` applies automatic 2D alignment across all molecules; `align=<mol-or-smiles>` aligns each molecule to a template. Route advanced alignment and coordinate generation to `../structure-generation/`.
- Extra `**kwargs` matching RDKit `MolDrawOptions` attributes are applied to the draw options; remaining kwargs are forwarded to the RDKit grid drawing call.

Common options:

| Option | Use |
| --- | --- |
| `legends` | Per-molecule labels under cells. A string applies to one molecule; use a list for grids. |
| `n_cols` | Molecules per row; datamol clamps it when fewer molecules are drawn. |
| `indices=True` | Draw atom indices for debugging highlight or atom-map tasks. |
| `bond_indices=True` | Draw bond indices when constructing `highlight_bond` lists. |
| `kekulize=False` | Work around aromaticity/kekulization failures for unusual molecules. |
| `max_mols` | Prevent very large grids from creating huge artifacts. |

### `dm.viz.match_substructure()`

Signature:

```python
dm.viz.match_substructure(mols, queries, highlight_bonds=True, copy=True, **kwargs)
```

Use when the user asks for ordinary substructure highlighting across one or more molecules and query molecules. `queries` should already be RDKit query molecules, usually from `dm.from_smarts()`. This helper computes matched atom and optional bond indices, then calls `dm.viz.to_image()` with forwarded drawing arguments such as `use_svg`, `n_cols`, and `mol_size`.

### `dm.viz.lasso_highlight_image()` / `dm.lasso_highlight_image()`

Signature:

```python
dm.viz.lasso_highlight_image(
    target_molecules, search_molecules=None, atom_indices=None,
    legends=None, n_cols=4, mol_size=(300, 300), use_svg=True,
    draw_mols_same_scale=True, r_min=0.3, r_dist=0.13,
    relative_bond_width=0.5, color_list=None, line_width=2,
    scale_padding=1.0, verbose=False, highlight_atoms=None,
    highlight_bonds=None, highlight_atom_colors=None,
    highlight_bond_colors=None, **kwargs,
)
```

Key behavior:

- `target_molecules` accepts one molecule/SMILES or a list. Empty strings and `None` targets raise `ValueError`.
- `search_molecules` accepts SMARTS strings, query molecules, lists of those, or `None`. SMARTS strings are converted with `dm.from_smarts()`. Invalid search molecules raise `ValueError`.
- `atom_indices` can be a flat list for one lasso region or a list of lists for multiple regions. Use it when exact atom indices are known and no SMARTS query is needed.
- `color_list` supports RGB/RGBA tuples in 0-1 or 0-255 style and hex strings. If there are more matched regions than colors, datamol cycles colors.
- `highlight_atoms`, `highlight_bonds`, `highlight_atom_colors`, and `highlight_bond_colors` are forwarded to the RDKit drawer for ordinary atom/bond highlighting in addition to lasso outlines.
- Unsupported RDKit draw-option names in `**kwargs` raise `ValueError`; valid names such as `bondLineWidth` are applied.
- `use_svg=True` returns an SVG string outside IPython. `use_svg=False` returns a Pillow image outside IPython.

### `dm.viz.conformers()`

Signature:

```python
dm.viz.conformers(
    mol, conf_id=-1, n_confs=None, align_conf=True, n_cols=3,
    sync_views=True, remove_hs=True, width="auto",
)
```

Use only for notebook-style 3D visualization of molecules that already have conformers. It requires optional `nglview` and `ipywidgets` packages. If `mol.GetNumConformers() == 0`, datamol raises `ValueError` with guidance to generate conformers first; route conformer generation to `../structure-generation/`.

### `dm.render_mol_df()`

Signature from installed inventory:

```python
dm.render_mol_df(df)
```

Renders molecule columns in a pandas DataFrame in-place for notebook display. Use after `dm.to_df(..., render_df_mol=True)` or after constructing a DataFrame with a molecule column. Do not assume it writes a file or returns a new DataFrame.

## Parallel and Job APIs

### `dm.JobRunner`

Signature:

```python
dm.JobRunner(
    n_jobs=-1, batch_size="auto", prefer=None, progress=False,
    total=None, tqdm_kwargs=None, **job_kwargs,
)
```

Use `runner(function, data, arg_type="arg", **fn_kwargs)` to dispatch work. `n_jobs=None`, `0`, or `1` is sequential. Other values use joblib. `prefer="threads"` is useful for IO-bound tasks, closures, notebook environments, or avoiding process-pickling failures. `prefer="processes"` uses process workers when callables and arguments are picklable.

### `dm.parallelized()`

Signature:

```python
dm.parallelized(
    fn, inputs_list, scheduler="processes", n_jobs=-1,
    batch_size="auto", progress=False, arg_type="arg", total=None,
    tqdm_kwargs=None, **job_kwargs,
)
```

`arg_type` controls how each input item is passed:

| `arg_type` | Input item shape | Call performed |
| --- | --- | --- |
| `"arg"` | `x` | `fn(x)` |
| `"args"` | `(x, y)` or `[x, y]` | `fn(x, y)` |
| `"kwargs"` | `{"x": 1}` | `fn(x=1)` |

### `dm.parallelized_with_batches()`

Signature:

```python
dm.parallelized_with_batches(
    fn, inputs_list, batch_size, scheduler="processes", n_jobs=-1,
    progress=False, arg_type="arg", total=None, tqdm_kwargs=None,
    flatten_results=True, joblib_batch_size="auto", **job_kwargs,
)
```

Use when the function expects a list/chunk of inputs. By default it flattens a list of batch results into one sequence. Set `flatten_results=False` when the caller needs one result per batch.

## Filesystem Utilities

`dm.utils.fs` wraps fsspec-backed paths. Use these helpers for local and supported remote paths without hard-coding filesystem separators.

| Function | Signature | Notes |
| --- | --- | --- |
| `get_cache_dir` | `get_cache_dir(app_name, suffix=None, create=True)` | Local user cache path; creates by default. |
| `get_mapper` | `get_mapper(path)` | Returns an fsspec mapper for a path/URI. |
| `get_basename` | `get_basename(path)` | Protocol-aware basename. |
| `get_extension` | `get_extension(path)` | Final suffix without the dot. |
| `exists` | `exists(path)` | True for files or dirs; file-like objects are treated as existing only by supported checks. |
| `is_file` | `is_file(path)` | Supports strings, path-like objects, `fsspec.OpenFile`, and file-like checks. |
| `is_dir` | `is_dir(path)` | Directory check through the path filesystem. |
| `get_protocol` | `get_protocol(path, fs=None)` | Normalizes common protocols such as `file`, `s3`, and `gs`. |
| `is_local_path` | `is_local_path(path)` | True when protocol is `file`. |
| `join` | `join(*paths)` | Joins using the separator from the first path's filesystem. |
| `get_size` | `get_size(file)` | Returns size or `None` when unsupported. |
| `copy_file` | `copy_file(source, destination, chunk_size=None, force=False, progress=False, leave_progress=True)` | Raises if source missing or destination exists without `force=True`. |
| `mkdir` | `mkdir(dir_path, exist_ok=False)` | Creates a directory through fsspec. |
| `md5` | `md5(filepath)` | Computes MD5 for a readable file. |
| `glob` | `glob(path, detail=False, **kwargs)` | Returns protocol-unstripped paths. |
| `copy_dir` | `copy_dir(source, destination, force=False, progress=False, leave_progress=True, file_progress=False, file_leave_progress=False, chunk_size=None)` | Copies directories, using datamol parallelization when filesystem classes differ. |

## Logging, Timing, Decorators, and Version Helpers

| API | Signature | Use |
| --- | --- | --- |
| `dm.without_rdkit_log` | `without_rdkit_log(mute_errors=True, mute_warning=True, mute_info=True, mute_debug=True, enable=True)` | Context manager that temporarily changes RDKit log status and restores previous state. |
| `dm.no_rdkit_log` | `no_rdkit_log(func=None, *, mute_errors=True, mute_warning=True, mute_info=True, mute_debug=True, enable=True)` | Decorator form for suppressing RDKit logs around a function. Supports `@dm.no_rdkit_log` and `@dm.no_rdkit_log()`. |
| `dm.disable_rdkit_log()` | no arguments | Globally disables all RDKit log levels until re-enabled. |
| `dm.enable_rdkit_log()` | no arguments | Globally enables all RDKit log levels. |
| `dm.utils.perf.watch_duration` | `watch_duration(log=True, log_human_duration=True)` | Context manager/decorator-style timing helper with `duration` and `duration_minutes` attributes after exit. |
| `dm.utils.decorators.disable_on_os` | `disable_on_os(os_names)` | Decorator that raises `NotImplementedError` on listed platforms; accepts `linux`, `osx`, `win`, or platform names. |
| RDKit version checks | `is_greater_than_current_rdkit_version(v)`, `is_greater_eq_than_current_rdkit_version(v)`, `is_lower_than_current_rdkit_version(v)`, `is_lower_eq_than_current_rdkit_version(v)` | Gate APIs that vary by RDKit release. |

## Boundary Notes

- This sub-skill owns visual artifacts and utility diagnostics, not molecule repair or dataset loading strategy. Route those upstream to `../molecule-io-prep/`.
- This sub-skill can show existing conformers, but it does not choose ETKDG settings, generate conformers, align 3D structures, or calculate SASA; route those to `../structure-generation/`.
- This sub-skill can render clustering or scaffold results if they are already computed, but it does not compute descriptors, scaffolds, MCS, or diversity picks; route those to `../fingerprints-similarity/` or `../structure-generation/`.
