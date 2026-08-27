# Gathering and Storage

Use this reference when a task asks how to collate multiple result JSONs, choose the correct `gather*` command, interpret TSV schemas, or inspect result storage APIs. For constructing or running quickrun commands, route to the CLI workflow sibling skill.

## Gather Command Selection

| Scenario | Command | Reports | Stability notes |
| --- | --- | --- | --- |
| RBFE/RHFE network from hybrid-topology results | `openfe gather` | `dg`, `ddg`, `raw` | Primary gather command. |
| ABFE result folders | `openfe gather-abfe` | `dg`, `raw` | Experimental; schema may change; `--allow-partial` is accepted but current ABFE aggregation still expects enough complete leg data for the chosen report. |
| SepTop result folders | `openfe gather-septop` | `dg`, `ddg`, `raw` | Experimental; supports current and legacy output structures; `--allow-partial` is accepted but current SepTop `dg`/`ddg` generation still expects enough complete complex/solvent data. |

Safe examples:

```bash
openfe gather results_parallel --report ddg --tsv
openfe gather results_parallel --report dg -o rbfe_mle.tsv
openfe gather-abfe abfe_results --report raw --tsv
openfe gather-septop septop_results --report dg -o septop_dg.tsv
```

All `gather*` commands recursively walk directories and collect files ending in `.json` that look like result JSONs by checking for an `estimate` key near the start of the file. Direct them at the highest folder that contains repeat folders or result JSONs; do not point them at trajectory/checkpoint directories unless JSON result files are also under that tree. Compressed `.json.gz` diagnostic files can be summarized with the bundled helper, but the OpenFE gather commands collect plain `.json` files.

## Repeat Folder Layouts

OpenFE commonly uses one repeat folder per independent repeat, especially for parallel/HPC execution:

```text
results_parallel/
  results_0/
    rbfe_<edge>_<leg>.json
    shared_*AnalysisUnit*_attempt_0/
      forward_reverse_convergence.png
      mbar_overlap_matrix.png
      replica_exchange_matrix.png
      replica_state_timeseries.png
      ligand_RMSD.png
      ligand_COM_drift.png
      structural_analysis.npz
    shared_*SimulationUnit*_attempt_0/
      checkpoint.chk
      simulation.nc
      simulation_real_time_analysis.yaml
  results_1/
    ...
  results_2/
    ...
```

Guidance:

- The `results_0`, `results_1`, `results_2` convention is expected by examples and works well with recursive gathering.
- Each repeat must have unique result and work directories; overwriting repeats makes uncertainty interpretation unreliable.
- Missing repeat folders do not always make `raw` reports fail, but `dg` and `ddg` can fail or warn depending on missing legs and `--allow-partial`.
- Keep result JSONs; large `.nc`, `.xtc`, `.chk`, and PDB artifacts are not needed for tabular summaries.

## RBFE/RHFE `openfe gather`

`openfe gather` is for relative binding or hydration free energy networks from hybrid-topology results.

Report schemas:

| Report | Columns | Meaning |
| --- | --- | --- |
| `raw` | `leg`, `ligand_i`, `ligand_j`, `DG(i->j) (kcal/mol)`, `MBAR uncertainty (kcal/mol)` | Per-leg, per-repeat free energy values. Failed rows use `Error`. |
| `ddg` | `ligand_i`, `ligand_j`, `DDG(i->j) (kcal/mol)`, `uncertainty (kcal/mol)` | Relative pairwise values after combining required legs. |
| `dg` | `ligand`, `DG(MLE) (kcal/mol)`, `uncertainty (kcal/mol)` | Maximum-likelihood absolute estimates from a connected relative network. |

Leg requirements:

- RBFE requires both `complex` and `solvent` legs for an edge.
- RHFE requires both `solvent` and `vacuum` legs for an edge.
- `dg` requires enough connected DDG edges for MLE; disconnected or too-small networks cannot produce valid absolute estimates.
- `--allow-partial` lets RBFE/RHFE gathering continue around missing or invalid edges, but `dg` still requires at least three connected pairwise edges and can fail if the remaining network is disconnected.

## ABFE `openfe gather-abfe`

`openfe gather-abfe` is for absolute binding free energy result JSONs. It prints an experimental-feature warning and exposes `--report`, `-o`, `--tsv`, and `--allow-partial` options.

Report schemas:

| Report | Columns | Meaning |
| --- | --- | --- |
| `dg` | `ligand`, `DG (kcal/mol)`, `MBAR uncertainty (kcal/mol)` or `std dev uncertainty (kcal/mol)` | Combined absolute binding free energy by ligand. Single-repeat reports use MBAR-style uncertainty; multi-repeat reports may use repeat standard deviation. |
| `raw` | `leg`, `ligand`, `DG (kcal/mol)`, `MBAR uncertainty (kcal/mol)` | Individual thermodynamic-cycle leg values. |

ABFE result parsing expects ligand names from serialized alchemical components and analysis-unit outputs such as `unit_estimate`, `unit_estimate_error`, `simtype`, and nonzero `standard_state_correction` when present. Current code filters setup/simulation units and uses analysis units when available.

## SepTop `openfe gather-septop`

`openfe gather-septop` is for separated-topology relative binding outputs. It prints an experimental-feature warning and exposes `--report`, `-o`, `--tsv`, and `--allow-partial` options.

Report schemas:

| Report | Columns | Meaning |
| --- | --- | --- |
| `raw` | `leg`, `ligand_i`, `ligand_j`, `DG(i->j) (kcal/mol)`, `MBAR uncertainty (kcal/mol)` | Raw complex/solvent leg values and corrections by ligand pair. |
| `ddg` | `ligand_i`, `ligand_j`, `DDG(i->j) (kcal/mol)`, uncertainty column | Relative binding differences. |
| `dg` | `ligand`, `DG (kcal/mol)`, uncertainty column | MLE absolute values centered around mean zero unless shifted externally. |

SepTop gathering has compatibility code for pre-v1.11 and current unit structures. When analysis units are present it skips setup/run units and uses analysis outputs with `unit_estimate`, `unit_estimate_error`, `simtype`, and standard-state correction fields. If a legacy and current output differ numerically, verify which version produced the JSONs before comparing tables.

## Network Aggregation Interpretation

For `dg` MLE reports:

- Values are relative absolute estimates centered around mean zero.
- Shifting to an experimental scale is an external analysis decision; do not imply the raw MLE table is already experimentally anchored.
- A disconnected network cannot produce meaningful global absolute estimates.
- Failed or missing edges may still appear as `Error` or omitted rows depending on report type and `--allow-partial`.

For uncertainty columns:

- `MBAR uncertainty` generally reflects per-leg estimator uncertainty.
- `std dev uncertainty` generally reflects repeat-to-repeat spread when multiple independent repeats exist.
- `uncertainty (kcal/mol)` in combined reports may be propagated across legs or generated by network/MLE tooling.
- Always state which report produced the uncertainty before comparing values.

## Result Storage APIs

OpenFE result storage exposes a client/server abstraction for external stores and metadata validation. Use it for storage-aware tasks; for ordinary quickrun summaries, direct JSON files are simpler.

Key concepts:

| Object | Responsibility |
| --- | --- |
| `ResultClient(external_store)` | High-level entry point for storing/loading transformations, networks, and result artifacts. |
| `ResultServer` | Coordinates external data with stored metadata; validates changes before loading. |
| `JSONMetadataStore` | Stores metadata in a `metadata.json` object within the external store. |
| `ResultClient.store_transformation()` / `store_network()` | Store gufe tokenizable setup objects with deduplicated keys. |
| `ResultClient.load_transformation()` / `load_network()` | Rebuild stored gufe tokenizable objects from keys. |
| `result_client[transformation][clone][extension][filename]` | Hierarchical access pattern for result artifacts. |

Storage troubleshooting clues:

- `MissingExternalResourceError` means metadata refers to data that the external store cannot provide.
- `ChangedExternalResourceError` means stored metadata no longer matches current external data; avoid `allow_changed=True` unless the user explicitly accepts changed external artifacts.
- `find_missing_files()` is useful for auditing metadata/data mismatches before analysis.
