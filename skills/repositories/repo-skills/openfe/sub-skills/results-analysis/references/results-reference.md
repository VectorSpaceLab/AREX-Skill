# Results Reference

This reference covers post-run interpretation of OpenFE result files and in-memory result objects. For running `quickrun` or creating repeat commands, use the sibling CLI workflow skill.

## Individual Quickrun Result JSONs

A completed `quickrun` produces a result JSON plus one or more shared output directories. The JSON is the lightweight summary to inspect first.

Core fields commonly present in result JSONs:

| Field | Meaning | Notes |
| --- | --- | --- |
| `estimate` | Protocol-level free energy estimate | Same conceptual value exposed by `ProtocolResult.get_estimate()`; usually unit-bearing. |
| `uncertainty` | Protocol-level uncertainty | Same conceptual value exposed by `ProtocolResult.get_uncertainty()`; usually unit-bearing. |
| `protocol_result` | Serialized protocol result data | Contains repeat/leg data used to compute the estimate. |
| `unit_results` | Per-unit outputs and exceptions | Use to distinguish failed runs, analysis units, setup units, and simulation units. |
| `source_key` | Unit provenance within `unit_results` entries | Newer outputs may contain Setup, Run/Simulation, and Analysis units; gather commands prefer analysis data when available. |

Decode OpenFE/gufe JSON with the gufe tokenization decoder when it is available:

```python
import json
from gufe.tokenization import JSON_HANDLER

with open("result.json") as handle:
    result = json.load(handle, cls=JSON_HANDLER.decoder)

estimate = result.get("estimate")
uncertainty = result.get("uncertainty")
```

The bundled helper [summarize_results_json.py](../scripts/summarize_results_json.py) uses this decoder when possible and falls back to standard JSON for diagnostic summaries.

## Python Result APIs

When working from Python execution rather than CLI outputs, a `ProtocolDAGResult` represents a single execution. One or more DAG results are passed to the protocol's `gather()` method to produce a `ProtocolResult`.

Typical pattern:

```python
protocol_result = protocol.gather([dag_result_0, dag_result_1, dag_result_2])
estimate = protocol_result.get_estimate()
uncertainty = protocol_result.get_uncertainty()
```

Important interpretation details:

- `get_estimate()` returns the protocol's free energy estimate with units.
- `get_uncertainty()` returns the protocol-specific uncertainty with units.
- A single repeat can yield zero standard deviation for repeat-based uncertainty; inspect MBAR/unit uncertainties when available.
- `Protocol.gather()` is an aggregation step over completed DAG results; it does not run simulations.

## Protocol-Specific Result Semantics

| Protocol family | Result meaning | Repeat/leg aggregation | Useful methods or fields |
| --- | --- | --- | --- |
| RBFE/RHFE hybrid topology | Relative free energy for one transformation leg; network gather combines complex/solvent or solvent/vacuum legs. | Mean estimate over repeats; repeat spread contributes uncertainty. | `get_estimate()`, `get_uncertainty()`, `get_individual_estimates()`, `get_overlap_matrices()`, `get_forward_and_reverse_energy_analysis()`. |
| ABFE | Absolute binding or solvation free energy with thermodynamic-cycle legs. | Binding combines complex and solvent legs plus standard-state correction; solvation combines solvent and vacuum legs. | `get_individual_estimates()` returns leg-keyed estimates; `get_estimate()` and `get_uncertainty()` combine legs. |
| SepTop | Relative binding free energy from separated-topology complex and solvent legs. | Complex and solvent legs include standard-state corrections before producing DDG and uncertainty. | `get_individual_estimates()`, `get_estimate()`, `get_uncertainty()`, energetic/structural analysis accessors. |
| Plain MD | Dynamics output rather than a free energy estimate. | No standard free energy estimate/uncertainty expectation. | Inspect trajectories/logs; do not expect `estimate` / `uncertainty` summary semantics. |

## Units and Numeric Values

OpenFE estimates and uncertainties are often `openff.units` quantities. They may print as values such as `-19.8 kilocalorie_per_mole` or expose magnitude/unit attributes. When summarizing:

- Preserve both value and unit when possible.
- Use kcal/mol column labels only for CLI gather outputs that explicitly report kcal/mol.
- Avoid stripping units silently; if a downstream table requires plain numbers, document the chosen unit.
- If a value has `.m` and `.u` attributes, `.m` is the magnitude and `.u` is the unit.

## Common Analysis Artifacts

Quickrun output directories can include analysis artifacts alongside the result JSON. These are useful for diagnosis but are not needed for simple summaries.

| Artifact | What it indicates | Use carefully |
| --- | --- | --- |
| `mbar_overlap_matrix.png` | MBAR overlap between lambda states. | Weak or disconnected overlap suggests poor sampling/convergence. |
| `forward_reverse_convergence.png` | Forward/reverse free energy convergence over increasing data fractions. | Agreement within uncertainty supports convergence; disagreement suggests more sampling or settings review. |
| `replica_state_timeseries.png` | Replica movement across lambda states. | Poor mixing or cliques can indicate sampling problems. |
| `replica_exchange_matrix.png` | Replica exchange transition matrix. | Present only for replica-exchange style simulations. |
| `ligand_RMSD.png` | Ligand RMSD over time. | Large drifts can indicate unstable binding pose or structural issues. |
| `ligand_COM_drift.png` | Ligand center-of-mass displacement. | Drift beyond several angstroms can indicate ligand movement from the binding site. |
| `protein_2D_RMSD.png` | Pairwise protein RMSD heatmap. | Bright spikes suggest structural transitions or instability. |
| `structural_analysis.npz` | Serialized structural analysis arrays. | Current structural analysis data is stored as NPZ, not JSON. |
| `simulation_real_time_analysis.yaml` | Real-time free energy analysis during simulation. | Diagnostic context; not a replacement for final result JSON. |
| `simulation.nc`, `checkpoint.chk` | Multistate trajectory and checkpoint files. | Large binary artifacts; not required for result table summaries. |

## Status-Like Fields

Result JSONs do not always have a single `status` field. Infer status from multiple signals:

- `estimate is None` or `uncertainty is None`: failed or incomplete result for gather purposes.
- Empty `unit_results`: failed or incomplete result.
- Every unit result contains `exception`: failed execution.
- Mixed unit results with setup/simulation/analysis entries: inspect source keys and exceptions before deciding.
- Valid estimate/uncertainty plus analysis warnings: result exists, but convergence/structural diagnostics may need review.
