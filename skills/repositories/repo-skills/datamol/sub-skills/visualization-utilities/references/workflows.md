# Visualization and Utility Workflows

These recipes are self-contained runtime guidance for future agents. They assume `import datamol as dm` and small, already-prepared molecule inputs unless a step explicitly says to route through another sub-skill.

## Render a Small Molecule Grid to SVG

Use SVG for deterministic, inspectable artifacts and headless environments.

```python
from pathlib import Path
import datamol as dm

mols = [dm.to_mol(smi) for smi in ["CCO", "c1ccccc1", "CC(=O)O"]]
legends = [dm.to_smiles(mol) for mol in mols]
outfile = Path("molecule_grid.svg")

image = dm.viz.to_image(
    mols,
    legends=legends,
    n_cols=3,
    use_svg=True,
    mol_size=(220, 180),
    outfile=str(outfile),
)

assert outfile.exists()
assert isinstance(image, str) or hasattr(image, "data")
```

Notes:

- If the input molecules come from a file or mixed table, use `../molecule-io-prep/` to parse, sanitize, and preserve properties before rendering.
- `outfile` writes through fsspec. Local paths are safest for portable examples.
- Use `max_mols` to cap large lists and avoid huge SVGs.

## Render PNG or Pillow Output

Use PNG when the user needs raster output or image-array checks.

```python
import datamol as dm

image = dm.viz.to_image("CCCO", legends="propanol", use_svg=False, mol_size=240)
image.save("propanol.png")
```

In notebook/IPython sessions, datamol may return IPython display objects instead of direct Pillow objects. For scripts and tests, prefer running outside notebooks or writing through `outfile`.

## Debug Atom and Bond Highlight Indices

Draw indices first, then pass exact indices.

```python
import datamol as dm

mol = dm.to_mol("CC(=O)Oc1ccccc1C(=O)O")
dm.viz.to_image(mol, indices=True, bond_indices=True, outfile="aspirin_indices.svg")
dm.viz.to_image(
    mol,
    highlight_atom=[0, 1, 2],
    highlight_bond=[0, 1],
    outfile="aspirin_highlight.svg",
)
```

If indices were derived from SMARTS rather than manually inspected, prefer `match_substructure()` or `lasso_highlight_image()`.

## Highlight a SMARTS Pattern with RDKit Grid Highlighting

Use `match_substructure()` for simple molecule/query matching and ordinary filled highlights.

```python
import datamol as dm

mols = [dm.to_mol("CC(=O)O"), dm.to_mol("CCN(CC)CC")]
query_smarts = "[C;H0]" "(=O)"
query = dm.from_smarts(query_smarts)
image = dm.viz.match_substructure(
    mols=mols,
    queries=query,
    highlight_bonds=True,
    use_svg=True,
    mol_size=(240, 180),
)
```

When no matches are found, the result may simply render unhighlighted molecules. Validate query intent separately when the user expects a required match.

## Create Lasso Substructure Highlights

Use `lasso_highlight_image()` for outline-style substructure highlights.

```python
import datamol as dm

svg = dm.viz.lasso_highlight_image(
    target_molecules=["CC(N)Cc1c[nH]c2ccc3c(c12)CCCO3", "c1ccccc1"],
    search_molecules="c1ccccc1",
    legends=["target", "benzene"],
    n_cols=1,
    use_svg=True,
    color_list=["#ff1472", (0, 0.5, 1, 1)],
)

with open("lasso.svg", "w", encoding="utf-8") as stream:
    stream.write(svg)
```

Use exact atom indices when the user already has atom selections:

```python
import datamol as dm

svg = dm.viz.lasso_highlight_image(
    "CC(N)Cc1c[nH]c2ccc3c(c12)CCCO3",
    search_molecules=None,
    atom_indices=[[4, 5, 6], [1, 2, 3, 4]],
    color_list=["#ff1472", "#1f77b4"],
)
```

Notes:

- `search_molecules` strings are SMARTS patterns, not ordinary labels.
- Invalid target molecules or invalid search patterns raise `ValueError`.
- Valid RDKit draw options such as `bondLineWidth` can be passed through; misspelled draw-option names raise `ValueError`.

## Render Molecule DataFrames

Use this for notebook display only, not file export.

```python
import datamol as dm

mols = [dm.to_mol("CCO"), dm.to_mol("c1ccccc1")]
df = dm.to_df(mols, mol_column="mol", render_df_mol=True)
dm.render_mol_df(df)
```

`dm.render_mol_df(df)` mutates display formatting in-place and returns nothing. For data export, route to `../molecule-io-prep/` and use dataframe/SDF/XLSX writers.

## Visualize Existing 3D Conformers

Only use this after conformers exist and optional notebook dependencies are available.

```python
import datamol as dm

# Molecule must already have conformers. Use ../structure-generation/ to create them.
view = dm.viz.conformers(mol, n_confs=3, n_cols=3, align_conf=True)
```

If datamol raises that the molecule has zero conformers, generate conformers first through `../structure-generation/`. If imports for `nglview` or `ipywidgets` fail, either install optional notebook visualization dependencies or fall back to 2D depiction with `to_image()`.

## Run Tiny Parallel Jobs Safely

Use sequential mode for deterministic debugging and threads for simple IO-bound or notebook-safe work.

```python
import datamol as dm

def smiles_length(smiles):
    return len(smiles)

sequential = dm.parallelized(smiles_length, ["CCO", "c1ccccc1"], n_jobs=1, progress=False)
threaded = dm.parallelized(
    smiles_length,
    ["CCO", "c1ccccc1"],
    scheduler="threads",
    n_jobs=2,
    progress=False,
)
assert sequential == threaded == [3, 8]
```

Use `arg_type` when inputs are tuples or dictionaries:

```python
import datamol as dm

def weighted_length(smiles, weight=1):
    return len(smiles) * weight

results = dm.parallelized(
    weighted_length,
    [{"smiles": "CCO", "weight": 2}, {"smiles": "CCN", "weight": 3}],
    arg_type="kwargs",
    n_jobs=1,
)
```

For very large iterables, use `parallelized_with_batches()` so each worker receives a chunk:

```python
import datamol as dm

def batch_lengths(smiles_batch):
    return [len(smiles) for smiles in smiles_batch]

lengths = dm.parallelized_with_batches(
    batch_lengths,
    ["CCO", "CCN", "CCCC"],
    batch_size=2,
    n_jobs=1,
)
```

## Use `JobRunner` Directly

Use `JobRunner` when the same execution policy is reused.

```python
import datamol as dm

runner = dm.JobRunner(n_jobs=2, prefer="threads", progress=False)
results = runner(lambda x: x * x, [1, 2, 3])
```

For process workers, replace lambdas and closures with top-level functions so joblib can pickle them.

## Check Paths with fsspec Helpers

Use `dm.utils.fs` for local paths and supported fsspec URIs.

```python
from pathlib import Path
import datamol as dm

output_dir = Path("viz_outputs")
dm.utils.fs.mkdir(output_dir, exist_ok=True)
path = dm.utils.fs.join(str(output_dir), "grid.svg")

dm.viz.to_image(["CCO", "CCN"], outfile=path, use_svg=True)
assert dm.utils.fs.is_file(path)
assert dm.utils.fs.get_extension(path) == "svg"
assert dm.utils.fs.get_protocol(path) == "file"
```

For remote URIs, ensure the matching fsspec backend and credentials are already configured by the user. Do not embed credentials in skill content or scripts.

## Control RDKit Logs During Noisy Probes

Use context managers for temporary muting.

```python
import datamol as dm

with dm.without_rdkit_log():
    mol = dm.to_mol("not-a-smiles")
```

Use a decorator for repeated functions:

```python
import datamol as dm

@dm.no_rdkit_log()
def parse_maybe_invalid(smiles):
    return dm.to_mol(smiles)
```

If global logs are disabled during diagnostics, restore them explicitly:

```python
import datamol as dm

dm.disable_rdkit_log()
try:
    # noisy operation
    pass
finally:
    dm.enable_rdkit_log()
```

## Run Environment Diagnostics

Use this quick probe before blaming visualization code:

```python
import datamol as dm

print("datamol import ok")
print("RDKit >= 2023.03:", dm.is_greater_eq_than_current_rdkit_version("2023.03"))
print("SVG type:", type(dm.viz.to_image("CCO", use_svg=True)).__name__)
print("PNG type:", type(dm.viz.to_image("CCO", use_svg=False)).__name__)
print("parallel ok:", dm.parallelized(lambda x: x + 1, [1, 2], n_jobs=1))
```

When process parallelism is involved, avoid lambdas in the diagnostic or set `scheduler="threads"`.

## Smoke Script

The bundled smoke script renders a tiny SVG, exercises fsspec path checks, runs a deterministic parallel mapping, and prints a JSON summary:

```bash
python scripts/visualization_utility_smoke.py --output-dir ./viz-smoke
```

Use `--scheduler threads --n-jobs 2` to check threaded joblib behavior. Use `--no-lasso` if only the base molecule grid should be tested.
