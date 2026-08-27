# Training troubleshooting

Use this guide for VLM-R1 GRPO failures that occur while building or launching training commands. Route JSONL content and reward-format failures to data-and-rewards unless the command wiring itself is wrong.

## Fast triage checklist

1. Re-render the command with `../scripts/launch_grpo_jsonl.sh` or `../scripts/render_multinode_torchrun.py` and inspect the exact flags.
2. Count colon-separated `data_file_paths`, `image_folders`, and `reward_method` values.
3. Check `global_batch = nproc_per_node * nnodes * per_device_train_batch_size`; it must be divisible by `num_generations`.
4. Confirm the selected model family matches the command: Qwen model names for Qwen routes, InternVL model names for InternVL routes.
5. Decide whether W&B should be enabled. If not, use `--no-wandb`.
6. For DeepSpeed failures, identify whether the job is using ZeRO-2, ZeRO-3, or ZeRO-3-offload and whether CUDA/NVCC is available.

## Command construction failures

### Mismatched data and image lists

Symptoms:

- Immediate `ValueError: Number of data files must match number of image folders`.
- Assertion about reward method count.

Fix:

- Use one `image_folders` item for each `data_file_paths` item.
- If `reward_method` is set, provide one method per JSONL file or omit it to use `default` for all files.
- For a single multi-image JSONL, still use one image root; the per-row `image` list is handled inside the loader.

### Invalid global batch for `num_generations`

Symptom:

- Trainer error saying the global train or eval batch size must be divisible by `num_generations`.

Fix:

- Compute `nproc_per_node * nnodes * per_device_train_batch_size`.
- Choose a `num_generations` divisor of that global batch.
- For 8 GPUs and batch size 8, global batch is 64, so `8` is valid. For 2 nodes with 8 GPUs each and batch size 1, global batch is 16, so `8` is valid.

### Wrong boolean spelling

Symptoms:

- Parser rejects a boolean flag or treats a value as the next argument.

Fix:

- The bundled launcher emits the same style used by the source recipes: `--bf16` as a flag, and booleans such as `--gradient_checkpointing true`, `--use_vllm False`, `--freeze_vision_modules true` as explicit values.
- Do not mix hyphenated and underscored names in a hand-edited command unless the parser has been tested with that spelling.

## CUDA memory and speed

### CUDA out of memory before generation

Likely causes:

- Full fine-tuning with too large `per_device_train_batch_size`.
- Large `max_completion_length` or high-resolution images.
- ZeRO-2 where ZeRO-3 is needed.
- FlashAttention unavailable, causing slower or more memory-heavy attention.

Fix order:

1. Lower `--per-device-train-batch-size`.
2. Lower `--max-completion-length`.
3. Lower Qwen `--max-pixels` or InternVL `--max-anyres-num` if image size is the memory driver.
4. Enable LoRA with `--use-peft true` and optionally `--freeze-vision-modules true`.
5. Move from ZeRO-2 to ZeRO-3, then consider ZeRO-3 offload if GPU memory still fails.
6. Reduce `--num-generations` only if the resulting value still divides global batch.

### OOM during generation with vLLM

VLM-R1 source launchers use `--use_vllm False`. If a user enables vLLM:

- Reserve a GPU or reduce `vllm_gpu_memory_utilization`.
- Ensure vLLM is installed and compatible with the CUDA/PyTorch stack.
- Do not combine vLLM with ZeRO-3 settings that explicitly disable gather-for-generation support.

### Slow ZeRO-3-offload training

ZeRO-3 offload moves optimizer and parameters through CPU memory. It can make an otherwise impossible run start, but it often becomes bandwidth-bound. Prefer LoRA/freeze or smaller image/token settings before relying on offload.

## DeepSpeed, CUDA, and FlashAttention

### DeepSpeed cannot find CUDA or NVCC

Symptoms:

- DeepSpeed import or op build fails with CUDA toolkit/NVCC errors.
- `CUDA_HOME` points to a location without `nvcc`.

Fix:

- Install or expose a CUDA toolkit matching the PyTorch stack.
- Set `CUDA_HOME` in the launch environment to a toolkit location that contains `bin/nvcc`.
- Keep toolkit paths in local shell configuration or job scripts; do not bake machine-specific paths into reusable skill files.

### FlashAttention import/build fails

Symptoms:

- Import errors for `flash_attn`.
- Build errors during package installation.
- Runtime failure when `--attn_implementation flash_attention_2` is passed.

Fix:

- Verify FlashAttention compatibility with the installed Python, PyTorch, CUDA, and GPU architecture.
- If the user only needs a static preview, render the command without launching.
- For an actual run, either repair FlashAttention or change attention implementation if the selected model stack supports a fallback. Expect slower and potentially larger memory use without FlashAttention.

### ZeRO-3 Qwen patch confusion

The entrypoint applies a Qwen2.5-VL forward monkey patch when the DeepSpeed path contains `zero3`. If a custom ZeRO-3 config name does not contain that substring, use a filename or path that clearly includes `zero3`, or verify the patching behavior in the launch log.

## W&B and debug logs

### W&B login or network errors

Symptoms:

- Training stalls or fails during W&B initialization.
- Missing API key errors.

Fix:

- If W&B is not required, use `--no-wandb` in the bundled launcher.
- If W&B is required, set the project/key outside the reusable skill files and keep credentials out of commands shown to others.

### Debug log path errors

Symptoms:

- Reward helpers fail while writing debug logs.
- Format/reward log files are missing.

Fix:

- Enable debug only when a writable log directory exists.
- The launcher creates the debug directory when executing; in dry-run mode it only shows the command.
- Turn off debug for minimal smoke tests.

## Data path and image loading failures

### Missing image files

Symptom:

- Assertion such as `Image paths do not exist` after dataset mapping begins.

Fix:

- The JSONL `image` field must be relative to the matching `image_folders` root.
- For multiple data files, verify each JSONL is paired with the image root for that dataset.
- For multi-image rows, every image listed in the row must exist under that one root.

### JSON instead of JSONL

Symptoms:

- JSON parsing fails line-by-line.
- Only the first line is read or the loader crashes early.

Fix:

- Convert to one JSON object per line. Route schema conversion/validation to data-and-rewards.

### Generic reward method with custom VLM reward enabled

Symptoms:

- Unsupported reward function for task type.
- GUI run fails when `is_reward_customized_from_vlm_module` is `true`.

Fix:

- For Qwen/InternVL REC, use custom VLM rewards.
- For generic GUI `all_match` or other generic methods, set custom VLM reward to `false` and pass `--reward_method` as needed.

## Model-family failures

### Unsupported model routing

Symptom:

- `Unsupported model` error.

Fix:

- Ensure `model_name_or_path` contains a supported family marker: `qwen`, `internvl`, or `glm`.
- For a new family, route to model-modules before constructing a training command.

### InternVL remote-code or image preprocessing errors

Fix:

- Use an InternVL model id/checkpoint that supports `trust_remote_code`.
- Lower `--max-anyres-num` if dynamic patches are too large.
- Keep `--attn-implementation flash_attention_2` only when the environment supports the converted InternVL FlashAttention path.

### GLM import mismatch

GLM routing exists, but the verified package set had a Transformers symbol mismatch for the GLM module. Do not promise GLM readiness unless the user's environment has a compatible Transformers/model implementation and a passing import smoke test.

## Multi-node rendezvous failures

### Missing or wrong master address

Symptoms:

- Nodes hang at rendezvous.
- Renderer error about missing master address.

Fix:

- In the host map, include the master node and its reachable address.
- If the master node is not in the map, pass `--master-addr` explicitly.
- Ensure every node can connect to the master port.

### Rank or node count mismatch

Symptoms:

- Some nodes wait forever.
- Duplicate rank errors.
- World-size mismatch.

Fix:

- Render all per-node commands from one host map so `--nnodes`, `--node_rank`, `--master_addr`, and `--master_port` are consistent.
- Launch exactly one command per listed node.
- Keep `nproc_per_node` identical unless the cluster setup has been deliberately adapted.

### Environment or file skew across nodes

Symptoms:

- Rank 0 starts, another rank fails importing packages or reading data.

Fix:

- Confirm every node has compatible Python packages, CUDA libraries, model/cache access, and data paths.
- Prefer shared storage or identical relative mounts.
- Keep per-node logs and compare the first failing rank rather than only the master log.
