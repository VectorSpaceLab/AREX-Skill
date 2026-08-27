# Troubleshooting

## vLLM on Windows

vLLM does not run natively on Windows in this repo guidance. Use WSL or Docker instead.

## CUDA or VRAM out of memory

Likely causes:

- The checkpoint is too large for the selected GPU memory.
- The selected `--max-model-len` exceeds the row recommended by the memory table.
- FP8 KV cache is missing where the table expects it.

Actions:

- Move to the lower-memory quantized row.
- Lower `--max-model-len` to the table value.
- Add `--kv-cache-dtype fp8` when the selected row calls for it.
- Reduce `--gpu-memory-utilization` only if you still need headroom after matching the table.

## Missing model path

Likely cause:

- The checkpoint directory was never downloaded, was renamed, or points at the wrong subdirectory.

Actions:

- Verify the path before printing or running a command.
- Make sure the path points at the actual model folder, not just a parent directory.
- Confirm whether the source checkpoint or the quantized copy should be used.

## `--max-model-len` is too high

Likely cause:

- The requested context length is not compatible with the chosen memory row.

Actions:

- Pick a supported row from the memory table.
- For 24GB maximum-context requests, use the 4-bit + FP8 row with `131072`.
- For 24GB precision-first requests, use the original-model row with `16384`.

## FP8 KV cache problems

Likely causes:

- The flag was added for a row that does not call for it.
- The backend or version combination does not accept the cache setting you chose.

Actions:

- Match the table first.
- Remove the FP8 flag when the selected row does not need it.
- Re-check the vLLM version if the row is otherwise correct.

## bitsandbytes or GPU issues

Likely causes:

- The runtime does not have a compatible CUDA GPU.
- The environment is missing the model libraries needed for quantization.
- A CPU-only inspection environment is being used for a GPU-only mutation step.

Actions:

- Treat quantization as a GPU-backed workflow.
- Verify the CUDA stack before attempting a real quantization run.
- Keep the bundled planner in dry-run mode until the environment is ready.

## API keys are embedded somewhere

Likely cause:

- A key was copied into a file, prompt, notebook, or container definition.

Actions:

- Replace it with an environment variable or secret manager entry.
- Rotate the leaked key if it was exposed outside the intended host.
- Rebuild images without secret literals.

## CJK chart text looks garbled

Likely cause:

- The output font used for charts is missing the expected Chinese font.

Actions:

- Install the SimHei font.
- Clear the matplotlib cache.
- Treat it as a downstream rendering problem, not a model-serving failure.

## Docker GPU start fails

Likely causes:

- NVIDIA Container Toolkit is missing.
- The container cannot see the mounted model directory.
- The host port is already occupied.

Actions:

- Install or repair the GPU container toolkit.
- Check the mount path and model path again.
- Choose another host port if 8000 is already taken.
