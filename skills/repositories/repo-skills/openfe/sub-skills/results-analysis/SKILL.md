---
name: results-analysis
description: "Analyze OpenFE result JSONs, gather RBFE/ABFE/SepTop outputs,
  interpret estimates and uncertainties, and troubleshoot partial or failed
  result sets safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Results Analysis

Use this sub-skill when the task starts after `quickrun` or Python protocol execution and asks what the result files mean, how to collate repeat/network outputs, or why result gathering failed. Stay read-only: inspect JSON, TSV, storage metadata, and analysis artifacts; do not run simulations or submit jobs.

## Route First

- Use this sub-skill for result JSON `estimate` / `uncertainty` fields, `ProtocolResult.get_estimate()`, `ProtocolResult.get_uncertainty()`, `Protocol.gather()`, CLI `gather*` reports, repeat folders, analysis plots, and result storage access.
- Route simulation execution, `quickrun`, repeat command generation, resume behavior, and scheduler scripts to [`cli-workflows`](../cli-workflows/SKILL.md).
- Route protocol choice, settings, repeat counts before execution, and OpenMM backend settings to [`protocols`](../protocols/SKILL.md).
- Route ligand network construction, atom mapping, graph outputs, and missing-edge planning before execution to [`network-planning`](../network-planning/SKILL.md).

## Safe Workflow

1. Identify the result type: individual quickrun JSON, repeat folder, RBFE network, ABFE results, SepTop results, or storage-backed artifact.
2. For individual JSON files, decode with `gufe.tokenization.JSON_HANDLER.decoder` when available and inspect top-level `estimate`, `uncertainty`, `unit_results`, and `protocol_result` fields.
3. For network folders, choose `openfe gather`, `openfe gather-abfe`, or `openfe gather-septop` based on protocol family before interpreting TSV columns.
4. Preserve units. OpenFE result estimates are usually unit-bearing quantities; convert only when the target report explicitly requests a unit.
5. Treat trajectory/checkpoint artifacts as optional evidence for deeper analysis, not as required inputs for summary tables.

## Reference Map

- [Results reference](references/results-reference.md): JSON anatomy, Python result APIs, estimates, uncertainties, units, and common analysis artifacts.
- [Gathering and storage](references/gathering-and-storage.md): CLI gather command selection, TSV schemas, repeat layouts, network aggregation, and result storage APIs.
- [Troubleshooting](references/troubleshooting.md): missing estimates, failed edges, partial repeats, corrupted JSON, legacy SepTop outputs, and large artifact handling.

## Bundled Helper

Use [`scripts/summarize_results_json.py`](scripts/summarize_results_json.py) for a safe, deterministic summary of one or more result JSON files:

```bash
python scripts/summarize_results_json.py results_0 results_1 --format tsv
python scripts/summarize_results_json.py edge_results.json --format json
```

The helper only reads local JSON or JSON.GZ files, uses the gufe JSON decoder when installed, extracts estimate/uncertainty/status-like fields, and emits JSON or TSV. It does not run OpenFE analysis, submit jobs, download data, or mutate files.
