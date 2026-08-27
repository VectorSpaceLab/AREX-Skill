# Evaluation Workflows

## Choose the Right Workflow

Use three separate evaluation modes:

1. **Prediction-output interpretation**: summarize `confidence_*.json`, `affinity_*.json`, or existing CSV outputs from a local `boltz predict` run. This needs no benchmark targets and can use the bundled summary script.
2. **Benchmark reproduction**: compare predicted structures to reference targets using structural and ligand metrics. This requires benchmark targets, matching output folders, and OpenStructure.
3. **Publication-style aggregation**: combine per-target benchmark metrics into top-1, oracle, average, and confidence-interval summaries. This requires complete per-model predictions and evaluation JSONs for every compared tool.

Do not mix these modes. A confidence/affinity summary helps inspect predictions, but it is not equivalent to lDDT, DockQ, ligand RMSD, or physical-validity benchmark reproduction.

## Boltz-2 Evaluation Status

The repository documentation states that updated Boltz-2 evaluation files, setup, and scripts are **coming soon**. Until a user provides newer assets, document Boltz-2 benchmark reproduction as unavailable from the public repo evidence and avoid inventing commands.

The available repository evaluation workflow is the older Boltz-1 workflow. It is still useful for understanding folder layout, OpenStructure requirements, top-1/oracle aggregation, and common metric names.

## Legacy Boltz-1 Benchmark Layout

The documented downloaded benchmark bundle used this organization:

```text
boltz_results_final/
├── inputs/
│   ├── casp15/
│   └── test/
├── targets/
│   ├── casp15/
│   └── test/
├── outputs/
│   ├── casp15/
│   └── test/
├── evals/
│   ├── casp15/
│   └── test/
├── results_casp.csv
└── results_test.csv
```

A usable benchmark folder must have all three of these aligned by target name:

- prediction structures under the appropriate `outputs/.../predictions/` or model-specific output folder;
- reference structures under `targets/...`;
- generated OpenStructure JSONs under `evals/...` if aggregation is the next step.

For raw Boltz prediction output directories, expect the model outputs under `predictions/<input-name>/` with model files plus confidence and optional affinity JSON files.

## OpenStructure Structural Evaluation

The legacy `run_evals.py` workflow is reference-only for this skill. It shells out through Docker to OpenStructure commands and expects OpenStructure version 2.8.0 for reproduction consistency.

The structural command compares model and reference structures with metrics such as:

- lDDT and backbone lDDT;
- QS-score, DockQ, interface/contact scores;
- rigid and patch scores;
- TM-score.

The ligand command compares ligand structures with:

- lDDT-PLI;
- ligand RMSD;
- substructure matching.

Only run this workflow when the user explicitly has matching benchmark targets, predictions, Docker/OpenStructure access, and accepts the external dependency. Otherwise, explain what is missing and use local output summaries instead.

## Aggregating Benchmark Results

The legacy aggregation flow computes per-target metrics across five samples and reports:

- **top-1**: the sample selected by the model confidence score;
- **oracle**: the best sample among generated samples for that metric;
- **average**: mean metric across samples;
- **length/count guards**: skip or warn when ligand/interface metric cardinality differs between tools.

For Boltz predictions, top-1 selection in the legacy aggregator comes from `confidence_<target>_model_<n>.json` and the `confidence_score` field.

Publication-style aggregation also compares multiple tools with shared target sets. It removes known CASP overlap with the authors' validation set but cannot guarantee no overlap with closed-source model validation sets.

## Physical-Similarity Checks

The legacy physical-similarity script is reference-only. It computes ligand distance-geometry violations, stereochemistry violations, ring/planarity violations, steric clashes, and an overall validity boolean, but the source script contains environment-specific data paths and depends on large chemistry/structure assets.

Do not copy or run it directly as a generic helper. If a user asks for physical-validity evaluation, first confirm they have the required CCD/molecule cache, parsed structures, matching targets, and a reproducible execution environment.

## Local Summary Workflow

Use the bundled script for safe local summaries of existing outputs:

```bash
python sub-skills/evaluation/scripts/boltz_evaluation_summary.py \
  --predictions-dir out/predictions \
  --out boltz_metric_summary.csv \
  --records-out boltz_metric_records.csv
```

For an existing benchmark CSV, either use long-form `metric,value` columns or let the script auto-detect numeric columns:

```bash
python sub-skills/evaluation/scripts/boltz_evaluation_summary.py \
  --csv results_test.csv \
  --out benchmark_metric_summary.csv
```

The script does not require OpenStructure, Boltz imports, model checkpoints, benchmark targets, or the original source repository. It only summarizes local JSON/CSV values that already exist.
