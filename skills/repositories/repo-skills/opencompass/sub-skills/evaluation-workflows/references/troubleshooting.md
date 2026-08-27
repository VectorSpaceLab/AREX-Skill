# Evaluation Workflow Troubleshooting

Use this guide for launch, resume, dry-run, and orchestration failures. Route config schema problems to `../../configuration-and-datasets/SKILL.md`, backend adapter/package issues to `../../model-backends/SKILL.md`, inference internals to `../../prompt-and-inference/SKILL.md`, and result-table analysis to `../../results-and-analysis/SKILL.md`.

## Missing or Wrong Config

Symptoms:

- The CLI exits before task planning.
- A config path cannot be found.
- `--mode eval` or `--mode viz` complains about missing reuse/station input.

Fixes:

- For file-based runs, pass a real `.py` config as the positional argument: `opencompass path/to/eval_config.py`.
- For shortcut runs, provide enough selectors: `--models ... --datasets ...` or HuggingFace flags plus `--datasets ...`.
- For eval-only or viz-only reruns, include `--reuse` or use station flags intentionally.
- Keep `-w` pointed at the base work directory, not the timestamp directory.

## Slow First Run or Downloads

Symptoms:

- The first execution appears stuck during dataset/model loading.
- HuggingFace or dataset network access blocks progress.
- Worker logs are hard to see in normal parallel mode.

Fixes:

- Start with `--debug` to run sequentially and keep output visible.
- Use the smallest model/dataset subset that reproduces the issue.
- Use `--dry-run` when the goal is only task planning or dataset/task resolution.
- Do not treat a successful CLI help check as proof that large model downloads or inference will work.

## Worker or GPU Allocation Confusion

Symptoms:

- Fewer tasks run than `--max-num-workers`.
- A local run appears underutilized.
- A user expects `--hf-num-gpus` to force exact GPU usage.

Fixes:

- Explain that `--max-num-workers` caps parallel tasks, but actual concurrency depends on available resources and per-task model requirements.
- Explain that `--hf-num-gpus` declares the minimum required GPUs for scheduling a HuggingFace model, not the exact number of GPUs OpenCompass consumes.
- For local runs, consider `--max-workers-per-gpu` when multiple small tasks can share a GPU.
- For clusters, confirm scheduler capacity separately from OpenCompass task counts.

## Slurm Partition Missing

Symptoms:

- `opencompass ... --slurm` fails immediately with an assertion about `--partition(-p)`.
- The user supplied `--partition` but jobs do not start.

Fixes:

- Always include `-p PARTITION` or `--partition PARTITION` with `--slurm`.
- Confirm the partition name with the cluster owner; do not guess it.
- If the config defines a non-Slurm runner, passing a Slurm partition may be ignored unless `--slurm` forces Slurm runner construction.
- Use `--dry-run --slurm -p PARTITION` first to validate command construction without submitting real work.

## DLC Configuration Missing

Symptoms:

- `opencompass ... --dlc` fails because the Aliyun/DLC config path does not exist.
- DLC submission starts but credentials/workspace/image values are rejected.

Fixes:

- Pass `--aliyun-cfg path/to/aliyun.cfg` and confirm the file exists in the user environment.
- Ask the user for DLC workspace/image/environment values; do not invent them.
- Keep DLC CLI installation and cloud credential setup outside this smoke workflow unless explicitly requested.
- Use `--dry-run` for command planning, but remember it cannot prove DLC credentials are valid.

## Reuse and Work Directory Mistakes

Symptoms:

- `--reuse` reports no previous results.
- Eval/viz stages cannot find predictions or results.
- A rerun creates a fresh timestamp instead of using prior artifacts.

Fixes:

- Use `-w` with the base work directory that contains timestamp folders.
- Use bare `--reuse` for the latest timestamp or `--reuse TIMESTAMP` for a specific one.
- Use `--mode eval --reuse` when predictions exist but evaluation did not finish.
- Use `--mode viz --reuse` when evaluation results exist but summary output is missing or stale.
- Preserve the same model/dataset abbreviations between the original run and the reuse run.

## Backend Override Warnings

Symptoms:

- OpenCompass warns that `infer` or `eval` config exists but `--slurm` / `--dlc` was also specified.

Fixes:

- Decide whether the config or CLI should own orchestration.
- If the config is authoritative, remove `--slurm` / `--dlc` and run the config as written.
- If the CLI is authoritative, keep the runtime backend flag and expect the stage runner to be replaced by the generated default backend config.

## Inspection Environment Cannot Run Models

Symptoms:

- CLI import/help works, but actual HuggingFace inference fails due to Torch/Transformers/backend compatibility.
- Optional accelerators such as vLLM or LMDeploy are missing.

Fixes:

- Distinguish CLI smoke validation from real model execution.
- Do not claim real HF inference was verified in a lightweight inspection environment.
- For actual inference, verify the target runtime has compatible Torch, Transformers, accelerator extras, CUDA/driver support, model weights access, and dataset access.
- For `-a vllm` or `-a lmdeploy`, confirm those optional extras are installed and the selected model supports the backend.

## Safe Debugging Order

1. `python scripts/opencompass_cli_smoke.py --check-help`
2. `opencompass path/to/eval_config.py --dry-run -w outputs/plan`
3. `opencompass path/to/eval_config.py --debug -w outputs/debug`
4. `opencompass path/to/eval_config.py --mode all -w outputs/run`
5. `opencompass path/to/eval_config.py --mode eval --reuse -w outputs/run`
6. `opencompass path/to/eval_config.py --mode viz --reuse -w outputs/run`
