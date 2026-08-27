# Training Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `--data` path is rejected or dataset is empty | Wrong directory nesting, unreadable files, or a zip that the loader cannot parse | Run the builder with `--validate-data-path`, inspect the first-level image files, and use a fresh output directory. A path check alone is not a dataset validation. |
| Image shape/config mismatch | Rectangle SHHQ data passed with `--square True`, or square data passed to `shhq` | Use `--square False` for 1024x512 SHHQ and keep the model/config consistent with the data geometry. |
| OOM on the first batch | Total batch or per-GPU batch is too large for the selected resolution | Reduce `--batch`, use `--batch-gpu` where supported, reduce GPUs only with a corresponding batch plan, and start a new debug run. |
| SG3 says required option is missing | `--cfg`, `--gpus`, `--batch`, `--gamma`, or `--data` omitted | Use the SG3 builder route; all of those options are required by the source CLI. |
| Training help or dry run fails before parsing | The selected training root is only the StyleGAN-Human patch-script directory or lacks `metrics/`, `training_loop.py`, `torch_utils/`, `dnnlib/`, or support dependencies such as `psutil` | Apply the modified StyleGAN-Human training files to a complete StyleGAN2-ADA/StyleGAN3 training root and pass `--training-root`; do not treat the patch directory as fully executable. |
| Training is unexpectedly slow | CPU fallback, too few GPUs, high-resolution rectangle model, workers/IO bottleneck, or a debug command being mistaken for paper-scale | Verify CUDA and device count, inspect the resolved options, keep dataset on fast storage, and report the actual GPU count/kimg. |
| Resume produces shape/key mismatch | Incompatible checkpoint, changed config, or changed geometry | Resume only from the same generator family/config and compatible image shape; otherwise start a new run and document the reason. |
| `ninja`/custom CUDA extension fails | CUDA toolkit/compiler mismatch or stale torch-extension cache | Check the PyTorch/CUDA/driver matrix, compiler, `CUDA_HOME`, and stale extension cache; do not treat a source import as a training pass. |
| Boolean options behave unexpectedly | Click bool parsing received an ambiguous value | Use explicit `True`/`False` or `1`/`0`, inspect the dry-run output, and record the resolved value. |
| Metrics or snapshot writing fails | Missing metric dependencies, unwritable output, or insufficient disk | Start with `--metrics none` where supported, verify output permissions and free space, and keep snapshots on a durable volume. |
| Run was stopped after writing a partial directory | Interrupted process or preemption | Inspect the last options/logs and checkpoint, then resume only after checking compatibility; do not overwrite the partial run blindly. |

Full training remains a required CUDA workflow. A successful command construction, parser help, or CPU import does not verify model training.
