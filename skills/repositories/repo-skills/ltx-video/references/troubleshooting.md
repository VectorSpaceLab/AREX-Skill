# Cross-cutting troubleshooting

Use the leaf troubleshooting document when the failure is clearly command/media-specific, config-specific, or inside a direct component. Use this page for environment and boundary failures that affect more than one route.

## Import or installation fails

1. Confirm Python is 3.10 or newer: `python --version`.
2. Confirm the command is using the intended interpreter: `python -m pip --version`.
3. For source-checkout inference, install with `python -m pip install -e ".[inference]"`. Core-only installs can omit media packages required by `ltx_video.inference`.
4. Run `python scripts/check_ltx_video_env.py --deep-imports`. Missing optional modules are reported without downloads. Add `--require-package` only in a gate that must fail when LTX-Video is absent.
5. Keep Transformers in the package-supported range recorded by the source metadata; avoid resolving unrelated global environments in place.

An import check proves only that Python can load the module. It does not prove checkpoint compatibility, media codec support, generation quality, or enough accelerator memory.

## No CUDA device or wrong device

- Run `python scripts/check_ltx_video_env.py --json` and inspect the PyTorch version, CUDA build, availability, count, and device names.
- A CPU result is valid for config inspection and some scheduler/component checks, but full generation is usually impractical.
- Use `--require-cuda` only when GPU execution is mandatory. Do not treat unavailable MPS on Linux as an error.
- If CUDA is expected but unavailable, verify that the PyTorch wheel matches the host driver/runtime and that the process can see the intended GPU before changing LTX-Video code.

## First run stalls, downloads, or fails offline

A YAML can reference a checkpoint, text encoder, prompt-enhancement models, and a spatial upscaler. These may be fetched separately from Hugging Face. Before running:

- inspect the YAML with `sub-skills/model-configs/scripts/inspect_ltxv_config.py`;
- decide whether network access is allowed;
- confirm authentication for gated assets and available cache/disk space;
- pass explicit local paths or use an already populated cache in offline environments;
- disable or avoid prompt enhancement when its models are not available.

The root environment checker intentionally never resolves or downloads these assets.

## Media or output errors

Install the `inference` extra and check imageio, PyAV, and torchvision availability. Codec support can still depend on the host FFmpeg/PyAV build. For argument-list mismatches, frame alignment, dimension padding, conditioning strength, and output naming, route to `sub-skills/local-inference/references/troubleshooting.md` and use its safe command builder.

## FP8 or Q8 kernel errors

FP8 YAMLs are optional accelerator-specific configurations. They require compatible hardware and external Q8/FP8 kernels that are not provided by the base project. If `q8_kernels` or a related operator cannot import, select the bfloat16 counterpart unless FP8 is an explicit requirement. Never report FP8 as verified based only on successfully parsing its YAML.

## Out of memory or unexpectedly slow generation

- Prefer a 2B or distilled configuration and reduce spatial/temporal size.
- Consider CPU offload only with the performance tradeoff made explicit.
- Account for multi-scale pipelines running two stages and loading a spatial upscaler.
- Close other GPU processes and recheck free memory immediately before generation.
- Do not silently change model family, precision, conditioning semantics, or output shape to make a request fit.

## Invalid or stale default config path

Always pass an explicit YAML that exists in the selected bundle/catalog. Do not rely on a code default whose filename may no longer exist in newer or older snapshots. Use the model-config catalog, validate the chosen file, then route execution to local-inference.

## Escalation information

When reporting a failure, include Python, package, PyTorch and CUDA versions; selected YAML; device; exact command; whether network/cache was allowed; traceback; and which checks were skipped. Never include credentials or access tokens.
