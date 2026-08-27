# Evaluation Troubleshooting

## `model_path` is invalid

- **Symptom**: the evaluation script exits early with an invalid model-path error.
- **Likely cause**: the path points to a missing local checkpoint directory or a hub id that is not reachable in the current environment.
- **Recovery**: confirm the checkpoint exists before launching the benchmark run.

## vLLM or TGI import/startup failures

- **Symptom**: `vllm` does not import, or the text-generation server does not start.
- **Likely cause**: the environment lacks the required CUDA-capable wheel or the launcher binary is missing.
- **Recovery**: verify the CUDA stack and the launcher binary first, then fall back to the other GPU path if one stack is unavailable.

## Out-of-memory during generation

- **Symptom**: generation exits or stalls when the model is loaded.
- **Likely cause**: the checkpoint is too large for the current GPU memory budget.
- **Recovery**: lower `gpus`, `gpu_memory_utilization`, or model size; keep the prompt length and `max_new_tokens` minimal for smoke checks.

## Metric scripts cannot compile predictions

- **Symptom**: compile/run metrics remain at zero or fail on every sample.
- **Likely cause**: the decompiled output is missing a function signature, includes malformed braces, or the toolchain is not installed.
- **Recovery**: check that the prediction files contain a compilable C function and that `gcc`, `g++`, and `objdump` are available.

## Edit similarity or output parsing fails

- **Symptom**: edit-similarity scripts cannot read the prediction directory or produce empty averages.
- **Likely cause**: the output root does not use the expected optimization-level layout or the file naming convention is off.
- **Recovery**: compare the generated layout to the output schema in the data-format reference.

## Legacy single-GPU path is confusing

- **Symptom**: a user asks about the single-GPU script in the README.
- **Likely cause**: that path is labeled legacy / not updated.
- **Recovery**: prefer the vLLM or TGI route unless the user explicitly wants to inspect the legacy path.
