# MMPA, Fraggle, and FreeWilson

These contributed workflows are useful for medicinal chemistry analysis, but they are optional script families. Do not assume they are importable from a binary RDKit installation unless the environment proves the specific modules and dependencies are present.

## MMPA Scripts

The contributed MMPA scripts generate matched molecular pairs from SMILES, canonicalize transforms, apply transforms, and optionally build/search a SQLite-backed pair index.

Input hygiene before MMPA:

- Remove mixtures and salts before fragmentation.
- Reject molecules containing `*` atoms unless the specific MMPA command expects attachment-point input.
- Canonicalize input SMILES with RDKit before MMP identification.
- Keep stable identifiers next to SMILES so results can be traced back to source compounds.

Core two-stage MMP workflow:

```bash
python rfrag.py < molecules.smi > fragmented.txt
python indexing.py < fragmented.txt > pairs.csv
```

Important `indexing.py` options:

- `-s` emits symmetrically equivalent forward and reverse pairs.
- `-m MAXSIZE` limits the maximum changed fragment size in heavy atoms.
- `-r RATIO` limits changed fragment size relative to compound size; `-m` overrides this when both are provided.

Transform utilities:

```bash
python cansmirk.py < transforms.smirks > canonical_transforms.txt
python mol_transform.py -f canonical_transforms.txt < molecules.smi > transformed.csv
```

Database workflow shape:

```bash
python create_mmp_db.py -p my_mmp -s < fragmented.txt
python search_mmp_db.py -p my_mmp -t mmp < query_molecules.smi > query_pairs.csv
```

Search types include `mmp`, `subs`, `trans`, `subs_smarts`, and `trans_smarts`. SMARTS-enabled database search depends on additional database/indexing support and can be slow for broad SMARTS patterns.

Use `../reactions-standardization/` instead when the task is core reaction SMARTS execution, R-group decomposition, or MolStandardize cleanup rather than the contributed MMPA script workflow.

## Fraggle Similarity

Fraggle is a contributed ligand-similarity workflow that fragments query molecules, searches fragments with Tversky similarity, and post-processes atom contributions into final Fraggle similarity scores.

Three-stage workflow shape:

```bash
python fraggle.py < query.smi > query_fragmentation.csv
python rdkit_tversky.py -f query_fragmentation.csv < library.smi > tversky_hits.csv
python atomcontrib.py < tversky_hits.csv > final_fraggle_results.csv
```

Expected data shapes:

- Query/library SMILES files use `SMILES ID` records separated by spaces or commas.
- Fragmentation output contains whole molecule SMILES, query ID, and fragment SMILES.
- Tversky output contains query fragment, query molecule, query ID, retrieved molecule, retrieved ID, and Tversky similarity.
- Final output includes retrieved SMILES/ID, query SMILES/ID, Fraggle similarity, and an RDK5 similarity field.

Operational notes:

- The Python Tversky script is convenient for small examples but can become the rate-limiting step for large libraries.
- The original guidance recommends using a chemistry cartridge or database-backed search for large-scale screening.
- Standard RDKit fingerprint similarity belongs in `../descriptors-fingerprints/`; use Fraggle only when the user specifically needs this fragment-aware contributed algorithm.

## FreeWilson

The contributed FreeWilson utility performs Free-Wilson analysis from a scaffold, aligned analog molecules, and activity scores, then builds predicted compounds from R-group combinations.

Typical API shape when the optional module is importable:

```python
from freewilson import FWDecompose, FWBuild, predictions_to_csv

decomp = FWDecompose(scaffold, mols, scores)
print(decomp.r2)
for pred in FWBuild(decomp, pred_filter=lambda value: value > 8):
    print(pred.smiles, pred.prediction)
```

Data and modeling requirements:

- Scores must be suitable for regression, such as pIC50 instead of raw IC50 values.
- The scaffold can be a scaffold molecule, SMARTS pattern, or list of scaffolds/patterns.
- The workflow can use `rdkit.Chem.rdFMCS` to find a scaffold, but review the MCS chemically before trusting predictions.
- Enumeration can grow quickly; use prediction, heavy-atom, molecular-weight, or molecule filters early.

Optional dependency notes:

- FreeWilson is commonly a source-tree contributed module, not guaranteed as a top-level installed module.
- Tests and full workflows may require scientific Python packages beyond RDKit, such as numpy/scipy/scikit-learn/tqdm depending on the implementation version.
- If the module is absent, explain the dependency gap rather than rewriting a regression/enumeration engine inline.

## Choosing Among These Tools

- Choose MMPA when the user asks for matched pairs, transformations, canonical SMIRKS, or MMP database search.
- Choose Fraggle when the user asks for fragment-aware ligand similarity from the contributed Fraggle algorithm.
- Choose FreeWilson when the user has an analog series, a scaffold/core, and numeric activities suitable for regression.
- Choose core RDKit descriptors/fingerprints when the user only needs generic similarity, clustering, or feature tables.
- Choose core reactions/R-group decomposition when the user needs reaction execution, product generation, R-group labeling, or standardization.
