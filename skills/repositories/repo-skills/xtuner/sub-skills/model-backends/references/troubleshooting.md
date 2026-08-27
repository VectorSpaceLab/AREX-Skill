# XTuner model-backends troubleshooting

Use this guide to separate safe config/import issues from real backend failures. Do not claim optional acceleration until the exact hardware, optional extension, and kernel path have been exercised.

## 1. Triage checklist

1. **Identify the backend tier.** Is the failing path config-only, CPU/import, CUDA, NPU, distributed EP, FP8, or RL/Ray? Route RL-specific rollout/advantage issues to reinforcement-learning.
2. **Run the safe checker.** From this sub-skill directory:

   ```bash
   python scripts/check_xtuner_backend.py --check-optional
   python scripts/check_xtuner_backend.py --json --expect-cuda
   ```

3. **Read warnings literally.** FlashAttention, bitsandbytes, DeepEP, AdaptiveGEMM, grouped GEMM, Triton, Ray, and NPU libraries are optional. Missing optional imports are not the same as a broken dense BF16 config.
4. **Decide CPU vs real backend.** CPU checks prove only config/import sanity. CUDA/NPU/distributed kernels require native tests or tiny training on target hardware.
5. **Record the unresolved gap.** If a dependency or device is missing, state which capability is unverified and choose a safe fallback.

## 2. Common symptoms

| Symptom | Likely cause | Safe checks | Resolution / fallback |
|---|---|---|---|
| `flash-attn is not installed, using flex_attention instead` | XTuner configured `flash_attention`, but FlashAttention import is missing on CUDA. | `python scripts/check_xtuner_backend.py --check-optional`; inspect `flash_attn` and `flash_attn_interface` status. | This is often a non-fatal fallback. Use `flex_attention` or install a Torch/CUDA-compatible FlashAttention package. Do not claim flash acceleration unless the flash import and a flash-backed test pass. |
| `Import FlashAttention 2 failed ... Please install it manually` | FlashAttention v2 import path is absent or ABI-incompatible. | Check `torch.__version__`, `torch.version.cuda`, Python version, and optional import status. | Install a matching wheel/build, or use `flex_attention` / `eager_attention`. If `XTUNER_USE_FA3=1`, also verify FlashAttention 3 interface imports. |
| bitsandbytes warns that no CUDA binary is available, especially for CUDA 13 | Installed bitsandbytes lacks a GPU extension matching the Torch CUDA version. | Run checker and read the `bitsandbytes` detail; compare `torch.version.cuda` to the bitsandbytes binary support. | Treat bitsandbytes GPU quantization/8-bit optimizers as unavailable. XTuner V1 BF16/FSDP model configs do not require bitsandbytes by default; avoid relying on BNB unless a compatible build is installed and tested. |
| `grouped_gemm` missing | Optional grouped GEMM package is not installed, or CUTLASS/fused permute path is unavailable. | Checker optional imports: `grouped_gemm`, `triton`; run only import-level probes first. | CUDA MoE may still use Triton grouped GEMM or torch fallbacks for token permute depending on config, but do not claim the fused grouped_gemm path. Install a compatible package or verify the Triton MoE tests on target GPUs. |
| `CPU GroupGemm is not implemented yet` | A MoE grouped GEMM path was executed on CPU. | Confirm `torch.cuda.is_available()` and XTuner device selection. | Use CPU only for config/import tests. Run MoE kernels on supported CUDA/NPU hardware, or keep the task at config-selection level. |
| AdaptiveGEMM import missing | Tile-wise FP8 linear/grouped-linear modules require `adaptive_gemm`. | Checker optional import: `adaptive_gemm`; attempt only safe import, not kernels. | Do not enable tile-wise FP8 acceleration. Use BF16 or install/verify AdaptiveGEMM on compatible hardware. |
| FP8 config builds but no speedup or handler warns unsupported | Device capability is below SM89/Hopper-class, `adaptive_gemm` missing, Triton incompatible, or no real kernels executed. | Checker reports CUDA capability and `torch.float8_e4m3fn` availability; run native FP8 tests only on target GPU. | Fall back to BF16. State that FP8 is config-only/unverified until SM89+ hardware and FP8 kernels pass. |
| `deep_ep` or `deep_ep_cpp` import error | `dispatcher="deepep"` selected without DeepEP installation. | Checker optional imports; avoid constructing `DeepEPDispatcher` until imports pass. | Use `dispatcher="all2all"` or `ep_size=1` for sanity. Install and verify DeepEP only on the intended distributed cluster. |
| AGRS dispatcher assertion about grouped router or `ep_size` | AGRS requires grouped router and a fixed grouping relationship. | Inspect `model_cfg.router.use_grouped_router`, `router_n_groups`, and `model_cfg.ep_size`. | For AGRS, configure grouped router and ensure `ep_size == router_n_groups == 8`. Otherwise use `all2all` or local EP. |
| NPU stack not installed | NPU-specific `torch_npu`/accelerator packages are absent. | Checker optional import: `torch_npu`; do not infer NPU support from CPU/CUDA imports. | Use CUDA/CPU fallback if available, or install the full NPU runtime and rerun native NPU smoke tests. |
| CUDA is not visible though Torch is installed with CUDA | Driver/toolkit/runtime mismatch, container not passed GPUs, or incompatible Torch build. | Checker reports `torch.version.cuda`, `torch.cuda.is_available()`, device count, and device names. Also run `nvidia-smi` outside Python if available. | Fix container GPU access/driver compatibility. Match optional extension wheels to the Torch CUDA build. Do not debug XTuner config until `torch.cuda.is_available()` is true for GPU tasks. |
| `no kernel image is available`, illegal instruction, or extension ABI error | Optional CUDA extension compiled for wrong GPU architecture, CUDA version, or PyTorch ABI. | Compare device capability, Torch CUDA version, and extension installation details. | Rebuild/install matching extension; fall back to non-fused path until native tests pass. |
| OOM after increasing TP/EP/sequence length | TP/EP do not reduce all memory components; VLM vision/projector and activations may dominate. | Check `tp_size`, `ep_size`, sequence length, micro-batch size, `recompute_ratio`, chunk loss, and VLM vision settings. | Start from smaller model/sequence/micro-batch. Use `CELossConfig(mode="chunk")`, recompute, or TP only when memory requires it. EP does not solve attention/activation memory. |
| HSDP config fails with EP | XTuner asserts HSDP requires `ep_size == 1`. | Inspect `FSDPConfig(hsdp_sharding_size=..., ep_size=...)`. | Disable EP or disable HSDP. Do not combine HSDP sharding with expert parallelism. |
| Unknown model alias returns `None` | Alias is not in XTuner's `model_mapping`. | Print alias resolution with `get_model_config(alias)`. | Instantiate the concrete config class directly or use `get_model_config_from_hf` for supported text HF model types. |
| VLM HF save config does not reflect modified values | Compose/VLM configs may not fully implement HF config conversion. | Check whether `hf_config` returns `None` or logs a warning. | Keep original HF config caveat in handoff. Verify saved `config.json` and weights before relying on VLM HF export. |
| `torch.compile` fails around optional kernels | Compiler interacts badly with a fused/optional op or dynamic shape path. | Retry with `compile_cfg=False` on model config and `FSDPConfig(torch_compile=False)` for isolation. | Use no-compile mode for debugging; re-enable only after optional kernels are verified. |

## 3. FlashAttention fallback details

XTuner attention configs commonly default to `attn_impl="flash_attention"`. On CUDA, many config objects check whether `flash-attn` or `flash-attn-3` is installed. If not, they log a warning and switch to `flex_attention`.

Operational consequences:

- A fallback warning does not automatically invalidate dense or MoE BF16 config work.
- It does mean FlashAttention throughput is unverified and should not be claimed.
- Flash-specific operations may still raise import errors if code forces the flash op rather than allowing the config fallback.
- For HF-parity debugging, set `attn_impl="eager_attention"` or run with `XTUNER_HF_IMPL=true`, but expect lower performance.

## 4. bitsandbytes and CUDA-version mismatch

bitsandbytes is optional for the XTuner V1 model-backends scope. If it warns that the installed package was compiled without GPU support or lacks a binary for the current CUDA version:

- Do not rely on BNB 8-bit optimizers, GPU quantization, or 8-bit matmul.
- This does not by itself block XTuner V1 BF16 FSDP model config selection.
- The fix is a bitsandbytes build matching the active Python, Torch, and CUDA runtime; otherwise leave BNB unavailable in the backend report.

## 5. Grouped GEMM, AdaptiveGEMM, Triton, and FP8

Grouped/MoE and FP8 acceleration combine several optional paths:

- CUDA MoE expert matmuls may use Triton grouped GEMM or optional CUTLASS/grouped_gemm paths.
- Token permute/unpermute can fall back when `grouped_gemm` is absent, but fused behavior is unverified until tested.
- Tile-wise FP8 ordinary linear and grouped-linear paths require AdaptiveGEMM.
- FP8 needs compatible CUDA hardware and dtype support; Hopper-class/SM89+ is the practical minimum indicated by XTuner's handler.
- Grouped FP8 paths can have shape/alignment constraints around 128-wide tiles/blocks.

Safe fallback order:

1. Keep model config BF16 without `float8_cfg`.
2. Verify CUDA visibility and Triton import.
3. Verify `adaptive_gemm` import and FP8 hardware capability.
4. Run the smallest native FP8/grouped-GEMM test available for the target install.
5. Only then enable `Float8Config` in the training config.

## 6. Dispatcher and EP availability

MoE dispatcher selection is safe only after topology checks:

- `ep_size=1`: local/naive dispatcher; useful for config sanity, not distributed EP performance.
- `all2all`: default EP path when an EP process group exists; requires distributed runtime and all-to-all support.
- `deepep`: requires DeepEP Python/C++ imports plus cluster/network setup. Missing imports should be reported as optional dependency gaps.
- `agrs`: requires grouped router and `ep_size == router_n_groups == 8` according to XTuner assertions.

When diagnosing EP:

1. Confirm world size and divisibility.
2. Confirm `model_cfg.ep_size == fsdp_cfg.ep_size`.
3. Confirm dispatcher-specific optional imports.
4. Run an EP-native smoke test before claiming correctness or speed.

## 7. CPU checks vs real backend verification

CPU checks are valuable for:

- `get_model_config` alias sanity.
- Pydantic config construction and field validation.
- Basic imports of `xtuner.v1.config`, `xtuner.v1.float8.config`, and model classes.
- Detecting absent optional packages without starting training.

CPU checks do **not** prove:

- FlashAttention works.
- CUDA grouped GEMM, Triton kernels, DeepEP, AdaptiveGEMM, or FP8 kernels work.
- NPU kernels work.
- MoE expert all-to-all behaves correctly on a real cluster.
- Full training memory or throughput is acceptable.

For real backend claims, require native tests or a bounded training smoke on the target hardware.

## 8. Minimal evidence language

Use precise statements:

- Good: "`Qwen3MoE30BA3Config` constructed and Torch reports one CUDA device; FlashAttention and AdaptiveGEMM are missing, so MoE FP8 acceleration is unverified."
- Good: "`dispatcher='all2all'` is the planned EP fallback; DeepEP is not installed, so do not use `dispatcher='deepep'`."
- Bad: "FP8 is supported" after only creating a `Float8Config`.
- Bad: "FlashAttention works" after seeing a fallback warning to `flex_attention`.
