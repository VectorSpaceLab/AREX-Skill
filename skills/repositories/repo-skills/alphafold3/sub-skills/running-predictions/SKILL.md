---
name: running-predictions
description: "Plan and run AlphaFold 3 predictions via Docker or local Python,
  including full runs, data-pipeline-only/inference-only splits, database/model
  setup, hardware and performance flags, and runtime diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Running AlphaFold 3 Predictions

Use this sub-skill when a user needs to execute or debug AlphaFold 3 prediction workflows. It covers command shape, setup prerequisites, stage splitting, database/model paths, HMMER tools, GPU/runtime tuning, and safe preflight checks.

## Route First

- For creating or validating AlphaFold 3 JSON input entities, use `../input-preparation/`.
- For interpreting ranking scores, confidence JSON, structures, embeddings, or distograms, use `../output-interpretation/`.
- For calling `folding_input`, `DataPipeline`, `ModelRunner`, or `process_fold_input` directly from Python, use `../python-apis/`.
- For CLI/Docker/local execution, database/model setup, hardware, and performance flags, stay here.

## Minimum Run Shape

AlphaFold 3 runs through `run_alphafold.py`. A full prediction needs exactly one of `--json_path` or `--input_dir`, an `--output_dir`, model parameters via `--model_dir`, and database paths via `--db_dir` or explicit database flags when the data pipeline runs.

Typical Docker command shape:

```bash
docker run --rm -it \
  --volume "$AF_INPUT:/root/af_input:ro" \
  --volume "$AF_OUTPUT:/root/af_output" \
  --volume "$AF_MODEL_DIR:/root/models:ro" \
  --volume "$AF_DB_DIR:/root/public_databases:ro" \
  --gpus all \
  alphafold3 \
  python run_alphafold.py \
  --json_path=/root/af_input/fold_input.json \
  --model_dir=/root/models \
  --db_dir=/root/public_databases \
  --output_dir=/root/af_output
```

Local Python command shape:

```bash
python run_alphafold.py \
  --json_path=fold_input.json \
  --model_dir=/path/to/model_parameters \
  --db_dir=/path/to/public_databases \
  --output_dir=/path/to/af_output
```

Use `scripts/build_run_command.py` to print a command without executing it. Use `scripts/check_runtime_requirements.py` to check imports, generated CCD resources, HMMER binaries, and optional model/database paths without downloading or mutating anything.

## Stage Selection

- Full prediction: keep both defaults, `--run_data_pipeline=true` and `--run_inference=true`.
- CPU data pipeline only: set `--run_inference=false`; this writes JSON augmented with MSAs/templates for later inference.
- GPU inference only: set `--run_data_pipeline=false`; input JSON must already contain precomputed MSA/template fields or explicitly empty values where appropriate.
- Reusing one output directory across split stages often needs `--force_output_dir=true` on the second stage.

## Operational Caveats

- Model parameters are external to the code package and must be obtained directly under the AlphaFold 3 model-parameter terms; do not assume they are bundled.
- Full public databases are external, large, and slow to download; plan hundreds of GB compressed and more when unpacked, preferably on SSD.
- Inference requires a CUDA-capable GPU in practice; A100/H100 80 GB are the best-supported high-throughput targets, while older GPUs need conservative settings.
- `python run_alphafold.py --help` can render flags but still exit non-zero because `--output_dir` is marked required; treat visible help text as useful even if the exit code is `1`.
- Outputs are theoretical predictions and model/output terms apply; do not present results as experimentally validated or clinically approved.

## References

- `references/cli-reference.md` groups the runtime flags by purpose.
- `references/setup-and-performance.md` explains setup, Docker/local execution, split workflows, sharding, GPU choices, and performance knobs.
- `references/troubleshooting.md` maps common runtime failures to concrete checks and fixes.
