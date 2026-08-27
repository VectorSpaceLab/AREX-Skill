# Performance and memory troubleshooting

Use this reference when Nunchaku performance controls fail at import, CUDA probing, model load, device placement, cache setup, qencoder setup, or benchmark planning. It is written for an installed package in a user project; it does not require access to the source checkout.

## Safe diagnostic command

```bash
python scripts/check_nunchaku_cuda.py --device cuda:0 --pretty
```

If CUDA allocation itself is risky on a shared host, add:

```bash
python scripts/check_nunchaku_cuda.py --device cuda:0 --skip-allocation --pretty
```

The JSON output should be saved with any bug report because it captures Python, Torch, CUDA runtime, visible devices, selected Nunchaku precision, and API availability without downloading models.

## CUDA unavailable or CPU-only host

Symptoms:

- `torch.cuda.is_available()` is false.
- Nunchaku imports but quantized model loading later fails.
- `get_precision()` raises because there is no CUDA device.

Likely cause: Nunchaku 4-bit workflows rely on CUDA kernels and supported NVIDIA tensor-core architectures. CPU is not a full substitute.

Actions:

1. Verify an NVIDIA driver is installed and visible to the Python environment.
2. Install a PyTorch build with CUDA support matching the host driver/runtime.
3. Re-run the checker. If CUDA remains unavailable, report a required-backend block instead of recommending CPU inference.

## Unsupported GPU architecture or wrong precision

Symptoms:

- Error mentions unsupported GPU architecture or lack of 4-bit tensor cores.
- Error asks for FP4 on Blackwell or INT4 on Turing/Ampere/Ada.
- A checkpoint filename contains `fp4` but the device expects `int4`, or the reverse.

Rules from `nunchaku.utils`:

- SM 120/121: use FP4 (`fp4`) models.
- SM 75/80/86/89: use INT4 (`int4`) models.
- Other SMs: unsupported by the quantized kernel compatibility check.

Actions:

```python
from nunchaku.utils import get_precision
precision = get_precision(device="cuda:0", pretrained_model_name_or_path=model_path_or_id)
```

Use the returned precision in the model asset path. Do not force a mismatched checkpoint because the loader performs hardware compatibility checks.

## Build or wheel CUDA mismatch

Symptoms:

- Import errors from compiled Nunchaku/CUDA extensions.
- Runtime errors such as no kernel image available for the device.
- A wheel works on one GPU family but not another.
- Blackwell devices fail with older PyTorch/CUDA combinations.

Evidence-backed constraints:

- Python >= 3.10.
- PyTorch >= 2.5 for general use.
- Linux CUDA >= 12.2; Windows CUDA >= 12.6.
- Blackwell requires PyTorch >= 2.7 and CUDA >= 12.8.
- Supported build targets include Turing SM 75, Ampere SM 80/86, Ada SM 89, and Blackwell SM 120/121 variants.
- A `FAST` source build may target only local GPUs. For a wheel meant to run across supported GPUs, build with `NUNCHAKU_INSTALL_MODE=ALL` and wheel-building enabled.

Actions:

1. Compare `torch.__version__`, `torch.version.cuda`, Python version, platform, and GPU capability from the checker output.
2. Install a Nunchaku wheel built for the same Python ABI, platform, PyTorch/CUDA family, and GPU architecture; or rebuild against the active PyTorch/CUDA environment.
3. For Blackwell, upgrade both PyTorch and CUDA runtime to the Blackwell-compatible minimum before debugging model code.
4. If only one GPU family fails, suspect a wheel built without that SM target.

## Turing / RTX 20-series failures

Symptoms:

- BF16 dtype errors or poor behavior on RTX 20-series.
- Attention implementation errors on Turing.
- Quantized T5 encoder path fails or is not supported.

Actions:

```python
transformer = NunchakuFluxTransformer2dModel.from_pretrained(
    quantized_transformer_path_or_id,
    offload=True,
    torch_dtype=torch.float16,
)
transformer.set_attention_impl("nunchaku-fp16")
# Build pipeline with torch_dtype=torch.float16, then use sequential CPU offload if offload=True.
```

Do not use the quantized T5 encoder as a Turing workaround; public docs state Turing support is pending for that encoder.

## Offload placement conflicts

Symptoms:

- Memory is not reduced after enabling offload.
- Errors after calling `.to("cuda")` together with `enable_sequential_cpu_offload()`.
- Qwen transformer is moved by Diffusers despite Nunchaku block offload.

Actions:

- For FLUX Nunchaku transformer offload, load with `offload=True`, construct the pipeline, and call `pipe.enable_sequential_cpu_offload()` without a manual `pipe.to("cuda")`.
- For Qwen low-VRAM mode, use `transformer.set_offload(True, use_pin_memory=False, num_blocks_on_gpu=1)`, exclude the transformer from Diffusers offload, then call sequential CPU offload.
- Tune `num_blocks_on_gpu` only after recording peak memory; larger values cost VRAM and can improve speed.
- If using pinned memory causes host-memory or driver issues, retry with `use_pin_memory=False`.

## Quantized T5 encoder failures

Symptoms:

- Loader errors about missing safetensors metadata/config.
- CPU device errors or CUDA-only failures.
- Strict state-dict loading failures.

Expected contract:

- `NunchakuT5EncoderModel.from_pretrained(...)` expects a safetensors file with metadata containing a serialized T5 config.
- It initializes the model on a meta device, replaces supported linear layers with W4 linear modules, then loads weights strictly.
- Default device is CUDA.

Actions:

1. Verify the path points to the quantized T5 safetensors file, not a directory of regular Transformers weights.
2. Use CUDA and an architecture supported by the encoder path.
3. Pass the encoder as `text_encoder_2` during FLUX pipeline construction; do not load it after the pipeline has already allocated the default T5 unless you are deliberately comparing memory.
4. On Turing, use offload and FP16 attention instead of qencoder.

## Cache setup or quality problems

Symptoms:

- No speedup from cache.
- Quality drift or LPIPS-like metric worsens.
- Cache-DiT import fails.
- Old TeaCache examples behave unexpectedly.

Actions:

- Ensure `apply_cache_on_pipe` is called after the pipeline's transformer is replaced with Nunchaku's transformer and before pipeline calls.
- Start with `residual_diff_threshold=0.12`; lower it for quality, raise it only with explicit acceptance of more drift.
- For double FB cache, tune `residual_diff_threshold_multi` and `residual_diff_threshold_single` separately.
- Cache-DiT requires `pip install cache-dit` and version compatibility with Diffusers; if unavailable, fall back to Nunchaku's built-in FB cache.
- Treat TeaCache as legacy/deprecated source evidence; if used, match `num_steps` to the actual denoising step count and set `model_name="flux-kontext"` for FLUX-Kontext.

## FP16 attention problems

Symptoms:

- Unexpected output or runtime error after `set_attention_impl("nunchaku-fp16")`.
- User wants to compare attention modes.

Actions:

```python
transformer.set_attention_impl("flashattn2")      # conservative/default
transformer.set_attention_impl("nunchaku-fp16")  # speed/Turing candidate
```

For a fair comparison, keep model asset, prompt, image size, seed, dtype, inference steps, guidance, offload, and cache settings fixed. Synchronize CUDA before timing.

## Multi-GPU and device-id issues

Symptoms:

- Model loads on one GPU but tensors are on another.
- `cuda:1` placement fails on a multi-GPU host.
- Memory appears allocated on device 0 despite targeting another device.

Actions:

- Pass the target device explicitly to precision selection and model loading: `get_precision(device="cuda:1")`, `from_pretrained(..., device="cuda:1")`.
- Use the same device for pipeline placement when not using sequential offload.
- Run the safe checker with `--device cuda:1` to confirm capability and allocation on that device.
- Treat `tests/flux/test_device_id.py` as a candidate verification case only when multi-GPU assets are available; do not claim it has run unless the verifier runs it.

## Benchmark claims

Do not claim speedups or memory ceilings from docs/tests as verified for the user's machine. When asked to validate performance:

1. Use a fixed prompt, seed, image size, step count, dtype, precision, attention mode, cache mode, qencoder flag, and offload flag.
2. Warm up before timing.
3. Call `torch.cuda.synchronize()` before stopping timers.
4. Reset peak stats before each memory case with `torch.cuda.reset_peak_memory_stats()`.
5. Report hardware, driver-visible CUDA, PyTorch CUDA version, Nunchaku version if available, and model asset identifiers.
