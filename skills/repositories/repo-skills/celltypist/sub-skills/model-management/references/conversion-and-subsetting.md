# Conversion and Subsetting

Use this reference before calling `Model.convert()` or `Model.subset()`. Both methods mutate the loaded `Model` object in place; write a new pickle afterward if the converted or subsetted model should be reused.

## Gene and Species Conversion

Verified signature:

```python
model.convert(
    map_file=None,
    sep=",",
    convert_from=None,
    convert_to=None,
    unique_only=True,
    collapse="average",
    random_state=0,
) -> None
```

What it changes:

- `model.classifier.coef_` is restricted or rebuilt for mapped features.
- `model.classifier.features` is replaced with the target feature names.
- `model.classifier.n_features_in_` is updated.
- `model.scaler.mean_`, `model.scaler.var_`, `model.scaler.scale_`, and `model.scaler.n_features_in_` are restricted or rebuilt to match.
- `model.description["date"]` is updated.

### Mapping Files

`map_file` must be a two-column mapping file. CellTypist accepts files without headers; if a header is present, it is read as a possible row and usually drops out because it does not overlap model features.

Built-in mapping files bundled with CellTypist include:

- `Ensembl105_Human2Mouse_Genes.csv`: default human-mouse or mouse-human mapping when `map_file=None`.
- `GENCODEv44_Gene_id2name.csv`: Ensembl gene ID to gene symbol mapping for human gene-ID/name conversion.
- Additional Ensembl 110 two-species maps for cynomolgus, human, mouse, pig, and rhesus combinations.

When `map_file` is a simple bundled filename, CellTypist searches its packaged sample-data directory. When it is a path, the file must exist at that path.

### Direction Selection

- If both `convert_from` and `convert_to` are omitted, CellTypist counts overlap between `model.features` and each mapping column, then converts from the column with greater overlap to the other column.
- If only one of `convert_from` or `convert_to` is supplied, it must be `0` or `1`; the other column is inferred.
- If both are supplied, the set must be `{0, 1}`.
- Invalid values raise `ValueError`.

For ambiguous maps, pass the direction explicitly and verify feature overlap before writing the converted model.

### 1:1 and 1:N Ortholog Handling

`unique_only=True` keeps only mappings that are unique in both columns. This is the conservative default and discards 1:N and N:1 mappings.

`unique_only=False` keeps non-unique mappings and requires a collapse strategy for targets that receive multiple source genes:

- `collapse="average"`: average classifier weights and scaler statistics across source genes.
- `collapse="random"`: choose one source gene's weights/statistics at random, seeded by `random_state`.

Any other `collapse` value raises `ValueError`.

### Human-to-Mouse Example With 1:N Orthologs

```python
from pathlib import Path
from celltypist import models

model = models.Model.load(Path("human_model.pkl").resolve().as_posix())
model.convert(unique_only=False, collapse="average")
model.write("mouse_model.pkl")
```

The saved model can then be passed to annotation as an explicit path; route annotation setup to [annotation-workflows](../../annotation-workflows/SKILL.md).

### Gene Symbols to Ensembl IDs

For query data whose variables are Ensembl IDs, convert a gene-symbol model to Ensembl IDs only when the mapping and species match the query data.

```python
from pathlib import Path
from celltypist import models

model = models.Model.load(Path("symbol_model.pkl").resolve().as_posix())
model.convert("GENCODEv44_Gene_id2name.csv", convert_from=1, convert_to=0)
model.write("ensembl_id_model.pkl")
```

If the model features are Ensembl IDs and the query uses symbols, reverse the direction with `convert_from=0, convert_to=1`.

### Conversion Checklist

Before conversion:

- Preserve the original model pickle; conversion is in place.
- Inspect `model.features[:10]` and a few mapping rows to confirm the namespace.
- Prefer explicit `convert_from` and `convert_to` for gene-ID conversions.
- Use `unique_only=True` for conservative cross-species conversion unless the user explicitly wants 1:N orthologs.

After conversion:

- Confirm that `len(model.features)` is nonzero and scientifically plausible.
- Confirm that `model.classifier.coef_.shape[1] == len(model.features)`.
- Confirm that `model.scaler.mean_.shape[0] == len(model.features)`.
- Write to a new filename rather than overwriting the original model.

## Cell-Type Subsetting

Verified signature:

```python
model.subset(keep_cell_types=None, exclude_cell_types=None) -> None
```

What it changes:

- `model.classifier.classes_` is restricted.
- `model.classifier.coef_` and `model.classifier.intercept_` are restricted to retained classes.
- `model.description["number_celltypes"]` and `model.description["date"]` are updated.
- Feature and scaler arrays are unchanged.

Constraints:

- At least one of `keep_cell_types` or `exclude_cell_types` must be provided; otherwise CellTypist logs a warning and returns without changing the model.
- `keep_cell_types` and `exclude_cell_types` may be a string or list-like values.
- `keep_cell_types` must contain at least two cell types.
- `exclude_cell_types` must leave at least two retained cell types.
- All requested cell types must exist in `model.classifier.classes_`.
- Keep and exclude sets must not overlap.

Example:

```python
from pathlib import Path
from celltypist import models

model = models.Model.load(Path("immune_model.pkl").resolve().as_posix())
keep = [label for label in model.cell_types if "T cell" in label or "NK" in label]
model.subset(keep_cell_types=keep)
model.write("immune_t_nk_subset.pkl")
```

Subsetting is convenient for narrowing a classifier's label space, but CellTypist documentation notes that retraining on the original reference data restricted to desired cell types is usually more accurate. Route retraining work to [training-and-custom-models](../../training-and-custom-models/SKILL.md).

## Mutation-Safe Pattern

Use copies at the file level rather than trying to undo in-memory mutations:

```python
from pathlib import Path
from celltypist import models

source = Path("source_model.pkl").resolve().as_posix()
model = models.Model.load(source)
model.convert(unique_only=True)
model.subset(exclude_cell_types=["unwanted_label"])
model.write("converted_subset_model.pkl")
```

If either conversion or subsetting fails, reload from the original pickle before retrying with different arguments.
