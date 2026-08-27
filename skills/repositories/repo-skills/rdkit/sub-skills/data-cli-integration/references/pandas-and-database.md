# Pandas and Database Integration

## PandasTools Molecule DataFrames

`rdkit.Chem.PandasTools` adds RDKit-aware helpers for pandas DataFrames. Import it when a task needs molecule columns, SDF/SMILES table round-trips, substructure filtering on a DataFrame, or molecule rendering in HTML/XLSX output.

Typical SDF load:

```python
import os
from rdkit import RDConfig
from rdkit.Chem import PandasTools

sdf_path = os.path.join(RDConfig.RDDataDir, "NCI", "first_200.props.sdf")
frame = PandasTools.LoadSDF(
    sdf_path,
    smilesName="SMILES",
    molColName="Molecule",
    includeFingerprints=True,
    strictParsing=True,
)
```

Important `LoadSDF` options:

- `molColName`: output column containing RDKit molecule objects; set to `None` to omit molecules.
- `smilesName`: optional output SMILES column.
- `includeFingerprints=True`: stores substructure fingerprints on molecules to speed DataFrame substructure filters.
- `removeHs`, `strictParsing`, and `sanitize`: forwarded to supplier behavior and should match the task's validation tolerance.
- `embedProps=True`: copies SDF properties onto molecule objects as well as DataFrame columns.
- `autoConvertStrings=True`: converts string properties to numeric/boolean types when possible.

Typical SMILES table flow:

```python
import pandas as pd
from rdkit import Chem
from rdkit.Chem import PandasTools

frame = pd.DataFrame({"name": ["ethanol", "pyridine"], "smiles": ["CCO", "c1ccncc1"]})
PandasTools.AddMoleculeColumnToFrame(
    frame,
    smilesCol="smiles",
    molCol="Molecule",
    includeFingerprints=True,
)
query = Chem.MolFromSmarts("[nH0]1cccc1")
matches = frame[frame["Molecule"] >= query]
```

The `>=` operator on molecule columns is monkey-patched as a substructure check. It returns `False` for `None` molecules. Validate parsed molecules before relying on downstream chemistry.

## Export and Rendering

Useful export helpers include:

- `PandasTools.WriteSDF(frame, out, molColName="ROMol", idName=None, properties=None, allNumeric=False)`.
- `PandasTools.SaveSMILESFromFrame(frame, outFile, molCol="ROMol", NamesCol="", isomericSmiles=False)`.
- `PandasTools.SaveXlsxFromFrame(frame, outFile, molCol="ROMol", size=(300, 300), dpi=96, formats=None)`.
- `PandasTools.FrameToGridImage(frame, column="ROMol", legendsCol=None, **kwargs)`.
- `PandasTools.ChangeMoleculeRendering(frame=None, renderer="image")` and `PandasTools.RenderImagesInAllDataFrames(images=True)` for HTML display behavior.

`PandasTools.molRepresentation` can be set to `"svg"` or `"png"` before `DataFrame.to_html()`. Rendering settings may be global to the Python session, so prefer frame-scoped rendering changes when possible.

`SaveXlsxFromFrame` needs an Excel writer dependency such as `xlsxwriter`. Treat XLSX export as optional and fail with an actionable dependency message if the package is unavailable.

## Database Helpers

RDKit includes legacy database utilities under `rdkit.Dbase`:

```python
from rdkit import RDConfig
from rdkit.Dbase.DbConnection import DbConnect

conn = DbConnect(RDConfig.RDDataDatabase)
rows = conn.GetData(table="simple_mols1", fields="*", randomAccess=0)
```

Relevant modules include:

- `rdkit.Dbase.DbModule`: chooses available database support, normally `sqlite3` in modern Python environments, with older `pyPgSQL` support when present.
- `rdkit.Dbase.DbConnection.DbConnect`: wraps a DB-API connection and provides `GetData`/`GetDataCount` convenience methods.
- `rdkit.Dbase.DbUtils`: text-to-database, database-to-text, table copy, and type-inference helpers.
- `rdkit.Dbase.DbInfo`: database/table/column metadata helpers.
- `rdkit.Dbase.StorageUtils`: RDKit-style id validation and registration helpers.

Keep examples SQLite-focused unless the user explicitly asks for PostgreSQL-era behavior. If a task needs the PostgreSQL cartridge, SQL functions inside PostgreSQL, indexes, or server-side chemistry search, route to cartridge-specific documentation rather than treating `rdkit.Dbase` as a replacement.

## Projects/DbCLI Boundary

`Projects/DbCLI` contains historical command-line scripts for creating/searching molecule databases from SDF/SMILES, including descriptor/fingerprint table generation. In a self-contained skill, treat those scripts as reference-only because they assume project files, descriptor calculator paths, and legacy database conventions that may not be installed with a binary RDKit package.

For new agent workflows, prefer small explicit Python scripts using installed `rdkit`, `sqlite3`, `PandasTools`, and the descriptor/fingerprint APIs owned by `descriptors-fingerprints`.
