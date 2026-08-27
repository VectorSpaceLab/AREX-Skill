# Troubleshooting

## Packaging and handler setup

- Missing `torch-model-archiver` / `model_archiver`: install the dependency before packaging.
- Missing handler path: packaging cannot archive without a handler file.
- Missing config or checkpoint: confirm the paths are local and paired for the same model family.
- Invalid model name: use a simple archive-safe name without path separators.
- Output folder points to a file: choose a directory target instead.

## Handler/runtime mismatch

- The bundled handler is only validated for SECOND-style LiDAR serving.
- It expects float32 point-cloud bytes with `load_dim=4` and `use_dim=[0, 1, 2, 3]`.
- If the user needs a different detector family, the bundle can still help with preflight checks, but runtime inference is not validated here.

## Log analysis problems

- JSON log required: non-JSON logs will not parse.
- Missing metric in `plot_curve`: check that the metric appears in the selected eval interval and that the log interval matches the training setup.
- If the user copied legacy doc flags, prefer `--eval` and `--eval-interval` from the current parser.

## FLOPs and benchmark problems

- The FLOPs helper does not implement the `multi` modality branch.
- The FLOPs helper can raise an import error when `mmcv` is too old for `get_model_complexity_info()`.
- FLOPs numbers are approximate and may omit custom ops.
- The benchmark helper requires CUDA and a valid `cfg.test_dataloader`.
- If `--samples` or `--log-interval` were passed explicitly and the helper misbehaves, remember that the current parser does not declare integer types for those flags.
- If `torch.cuda.synchronize()` fails, the host is not suitable for this helper.

## Conversion and publish problems

- Legacy checkpoint migration scripts use strict loading; shape or key mismatches mean the source checkpoint is not the expected version.
- The checkpoint publishing helper removes optimizer state; keep the original checkpoint if training must resume.
- The release filename builder strips the old suffix before adding the hash suffix, so verify the final basename if you need exact naming.
- Conv+BN fusion changes the checkpoint weights; do not use it on checkpoints you still need in unfused form.

## Stop conditions

Stop after preflight if:

- the checkpoint is missing,
- the handler is unavailable,
- the requested serving family is outside the validated handler scope,
- required CUDA or custom ops are missing for the helper being requested,
- or the user only wants artifact validation and not execution.
