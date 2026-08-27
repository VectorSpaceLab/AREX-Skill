# Cross-cutting Composer troubleshooting

Use this file before diving into a sub-skill when installation, imports, optional dependencies, hardware, CLI behavior, or broad package routing are unclear.

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'composer'` | The public distribution is `mosaicml`; the import name is `composer`. | Install with `pip install mosaicml`, then retry `import composer`. |
| `PackageNotFoundError: mosaicml` but `import composer` works | A local source tree is shadowing package metadata. | Use a clean environment and install the package distribution; avoid relying on the current directory. |
| PyTorch/torchvision dependency conflicts | Installed torch/torchvision versions do not satisfy Composer's version window. | Install a compatible torch/torchvision pair before reinstalling `mosaicml`. |
| `numpy` or `Pillow` conflicts after installing torch | A torch/torchvision install selected newer dependencies than Composer allows. | Reinstall `mosaicml` or pin compatible `numpy<2.3` and `Pillow<12`. |
| Import succeeds but optional class fails | Optional extra missing. | Install only the matching extra, such as `mosaicml[nlp]`, `mosaicml[wandb]`, `mosaicml[onnx]`, or `mosaicml[libcloud]`. |

## Optional dependency map

- HuggingFace/Transformers model wrapper: `mosaicml[nlp]`; PEFT adapters: `mosaicml[peft]`.
- TensorBoard: `mosaicml[tensorboard]`.
- Weights & Biases, MLflow, Comet ML, Neptune: `mosaicml[wandb]`, `mosaicml[mlflow]`, `mosaicml[comet_ml]`, `mosaicml[neptune]`.
- Object-store and cloud/file upload helpers: `mosaicml[streaming]`, `mosaicml[libcloud]`, `mosaicml[oci]`, or provider-specific credentials.
- ONNX export validation: `mosaicml[onnx]` plus runtime/provider checks.

Do not install `mosaicml[all]` reflexively; it is a broad troubleshooting hammer that can introduce unrelated dependency conflicts.

## Backend and hardware failures

- CPU is enough for API, model/data, method-placement, logger, and export-smoke debugging.
- CUDA-specific behavior needs CUDA-enabled PyTorch, a visible GPU, compatible driver/runtime, and a small tensor allocation test.
- `device="gpu"` failing while `torch.cuda.is_available()` is false means the issue is below Composer: driver, container GPU passthrough, CPU-only torch wheel, or missing runtime libraries.
- `device_train_microbatch_size="auto"` only catches many CUDA OOMs during Trainer forward/backward. It does not fix dataloader, callback, model-construction, CPU, or non-CUDA memory errors.
- FSDP/FSDP2/tensor parallelism depends on world size, backend initialization, model wrapping policy, precision, checkpoint type, and PyTorch version. Route to `../sub-skills/distributed/SKILL.md`.

## CLI failures

- `composer --version` should print `MosaicML Composer <version>`.
- `composer -n N train.py ...` launches child processes; verify `python train.py ...` first.
- `composer_collect_env` prints an environment report rather than ordinary help output.
- `composer_validate_remote_path` expects a remote URI; `--help` is treated like a path in the source version used for this skill.
- If CLI subprocesses use the wrong Python, run from an environment where that environment's `bin` directory is first on `PATH`.

## Data/model workflow failures

- `ComposerClassifier` expects `(inputs, targets)` batches and needs `num_classes` unless the module exposes it or metrics are supplied.
- Custom batch schemas require subclassing `ComposerModel` or wrapping the loader in `DataSpec`.
- Mismatched checkpoint weights require a deliberate choice between full-state resume, weights-only load, non-strict model weights, or ignored keys.
- Dict-shaped batches for algorithms usually need `input_key` and `target_key`.

## File and artifact failures

- Checkpoint save/load mechanics belong to `sub-skills/training/`.
- Remote upload destinations, file logger placeholders, and profiler traces belong to `sub-skills/observability/`.
- Inference artifacts and export validation belong to `sub-skills/inference-export/`.
- Multi-rank filename collisions usually mean `{rank}` or `{local_rank}` was omitted from file names.

## Minimal recovery sequence

1. Run `python scripts/check_import.py` from the root skill directory.
2. If GPU behavior matters, run `python scripts/check_import.py --require-cuda` and `python sub-skills/distributed/scripts/device_probe.py`.
3. Run only the sub-skill smoke script for the failing workflow.
4. If a smoke passes but the user's job fails, compare inputs, optional extras, credentials, backend, and output paths before changing Composer APIs.
5. If the task requires external services, credentials, long training, or shared storage mutation, ask for explicit approval before running it.
