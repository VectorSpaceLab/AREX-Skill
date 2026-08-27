# gget API overview

Read this when a task crosses modules or when choosing between the Python API
and CLI. Detailed module contracts live in the linked sub-skills.

## Public Python exports

`import gget` exposes the principal operations: `ref`, `search`, `info`, `seq`,
`blast`, `blat`, `muscle`, `diamond`, `enrichr`, `archs4`, `pdb`, `virus`,
`elm`, `cellxgene`, `bgee`, `cbio_search`, `cbio_plot`, `cosmic`, `mutate`,
`opentargets`, `g2p`, `specificity`, `psi_block`, `gene_expression`,
`alphafold`, `gpt`, and `setup`. The package version is available as
`gget.__version__`.

## Return conventions

| Family | Typical return | Important distinction |
|---|---|---|
| Annotation/search | pandas `DataFrame`, JSON-compatible list/dict, or `None` | `json=True` changes the structured representation; it does not freeze upstream schemas. |
| Sequence retrieval | list of FASTA strings | `translate=True` selects UniProt protein records; otherwise Ensembl nucleotide records are used. |
| Remote similarity/portal queries | DataFrame or JSON records | Network, rate limits, and current database contents affect values. |
| Local alignment | `muscle` writes an `.afa` or prints; `diamond` returns structured results and can write output | Check local executable permissions and input orientation. |
| File/database operations | `pdb` returns text/JSON; `virus`, `alphafold`, and some save modes write files/folders | Always choose a new output path and inspect files after completion. |
| Plotting | `enrichr` can plot; `cbio_plot` saves/displays a heatmap and returns a boolean | A figure is not a tabular result; preserve the data/query parameters separately. |

## Boolean and output differences

Python APIs generally use positive booleans (`ncbi=False`, `translate=True`,
`save=True`). CLI flags are not always direct spellings: for example, `gget
info --ncbi` disables the NCBI provider, while Python `ncbi=True` enables it.
Use `gget <command> --help` instead of guessing a CLI spelling.

Python `save=True` often writes a module-defined filename in the current
working directory. Prefer an explicit CLI `--out` or Python `out=` path when the
operation supports it. For stable automation, capture returned structured data
and write it yourself after checking its schema.

## Chaining patterns

1. Resolve free text with `search(searchwords, species, limit=...)`.
2. Confirm the selected ID with `info(ens_id, ...)`, including the current
   Ensembl version and canonical transcript when relevant.
3. Retrieve a nucleotide/protein sequence with `seq(...)`, or route the ID to
   `archs4`, `bgee`, `cellxgene`, `opentargets`, or `g2p` as appropriate.
4. Send a bounded literal or FASTA sequence to `blast`/`blat`/`muscle`/`diamond`,
   or use `pdb`/`g2p` for structure-related annotations.

Do not use `cosmic` as a substitute for `mutate`, or `pdb` as a substitute for
`info(..., pdb=True)`: they answer different questions and have different
outputs and service constraints.

## Minimal verification

```bash
python -c "import gget; print(gget.__version__)"
gget --version
gget --help
```

For a Python call, print the type and a small shape/length summary rather than
assuming the service returned a non-empty DataFrame:

```python
result = gget.info("ENSG00000130234", verbose=False)
print(type(result), getattr(result, "shape", None))
```
