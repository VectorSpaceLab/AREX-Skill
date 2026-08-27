# Big-Model Inference Troubleshooting

## Checkpoint Path or Index Errors

Symptoms:

- `FileNotFoundError` for checkpoint shards or index files.
- Missing or unexpected keys during loading.
- A folder is accepted but Accelerate cannot identify the unique sharded index.

Actions:

- Confirm `checkpoint` points to one of: a single state-dict file, a sharded checkpoint `.json` index, or a folder containing one index plus the referenced shard files.
- For sharded checkpoints, verify every tensor name in the index maps to an existing shard filename.
- Set `strict=True` in `load_checkpoint_and_dispatch` or `load_checkpoint_in_model` when the goal is to surface key mismatches early.
- Do not ask future agents to run original examples to fetch checkpoints; require explicit user approval before downloads.

## Missing or Bad Offload Folder

Symptoms:

- Errors when a `device_map` contains `"disk"`.
- Offloaded weights fail to save, reload, or memory-map.

Actions:

- Provide a writable `offload_folder` to `load_checkpoint_and_dispatch` whenever disk offload is possible.
- Use `offload_dir` with `dispatch_model` and `offload_dir` with `disk_offload`.
- Keep offload folders out of source-controlled runtime skill directories.
- If the whole model is assigned to `"disk"`, switch from `dispatch_model` to `disk_offload`.

## Invalid Device Map

Symptoms:

- `check_device_map` fails because modules are uncovered or keys are invalid.
- Runtime device mismatch errors appear after manual mapping.

Actions:

- Run `check_device_map(model, device_map)` before loading large checkpoints.
- Remember manual map keys are module prefixes. Use `""` only when intentionally mapping the entire model.
- Use destinations supported by the environment: accelerator indexes, device strings, `"cpu"`, or `"disk"`.
- Inspect `model.hf_device_map` after dispatch; it is the authoritative resulting map.

## `no_split_module_classes` Problems

Symptoms:

- Residual blocks are split across devices and fail at runtime.
- Automatic mapping fragments a layer that should move as one unit.

Actions:

- Pass class names such as `"Block"`, `"DecoderLayer"`, or the model's residual block class, not attribute names like `"layers.0"`.
- Add tied-weight or residual-containing block classes when activations or shared weights cross device boundaries unexpectedly.
- Use `clean_result=False` and `verbose=True` in `infer_auto_device_map` to inspect why modules were split.

## Meta Tensor Misuse

Symptoms:

- Errors such as inability to copy data out of a meta tensor.
- `.to("cpu")`, `.cuda()`, or forward pass fails immediately after `init_empty_weights`.

Actions:

- Treat models built under `init_empty_weights` as skeletons only.
- Load real weights with `load_checkpoint_and_dispatch`, `load_checkpoint_in_model`, or manually set tensors before moving or running the model.
- Use meta models for `compute_module_sizes`, `infer_auto_device_map`, and memory planning.

## Memory Estimate Expectations

Symptoms:

- A model fits according to a size estimate but fails during actual generation or inference.
- GPU memory usage is higher than total parameter size.

Actions:

- Explain that weight-size estimates do not fully include activations, KV cache, temporary kernels, input batches, tokenizer/model-library overhead, or fragmentation.
- Check the largest layer size; offloaded execution still needs staging room for the largest layer on the execution device.
- Re-estimate with the intended dtype and with realistic `max_memory` limits.

## Pipeline Split Points

Symptoms:

- `prepare_pippy` tracing fails, output appears only on the last process, or split points are poor.

Actions:

- Provide realistic `example_args` matching the intended forward signature and batch dimensions.
- Prefer positional example arguments for experimental pipeline paths.
- Set explicit `split_points` if `"auto"` produces unexpected partitioning.
- Use `gather_output=True` only when every process needs the output; otherwise inspect output on the last process.

## Optional Libraries, Downloads, and Hardware

Symptoms:

- Import errors for `transformers`, `diffusers`, `timm`, or pipeline-related PyTorch features.
- Examples try to download Hub models or require GPUs.

Actions:

- Keep diagnostics on tiny local `torch.nn.Module` classes unless the user requested a specific model library.
- Ask before network access, Hub downloads, or GPU-only examples.
- Route launch/config syntax to `../configuration-and-cli/` and DeepSpeed ZeRO choices to `../distributed-training-backends/`.
