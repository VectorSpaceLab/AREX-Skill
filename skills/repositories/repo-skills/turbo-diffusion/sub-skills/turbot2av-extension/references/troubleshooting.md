# TurboT2AV Troubleshooting

Use this matrix for TurboT2AV extension issues only. Route core Wan T2V/I2V generation, Wan checkpoint conversion, and generic TurboDiffusion CUDA operator build questions to the appropriate sibling guidance.

## Quick triage

1. Confirm the user is in a TurboT2AV/LTX environment, not the core Wan TurboDiffusion environment.
2. Confirm the command can import `ltx_distillation.tools.run_av_inference_eval`.
3. Confirm `TURBO_CHECKPOINT_PATH` points to the LTX-2 base checkpoint and `TURBO_GEMMA_PATH` points to a local Gemma directory.
4. For student runs, confirm `--student_checkpoint` is supplied and points to the TurboT2AV student checkpoint.
5. Confirm the prompts file is plain text or a CSV with a `prompt`, `caption`, or `text` column.
6. Confirm CUDA is available for real inference. Parser/help checks can be CPU-only if dependencies import, but generation requires CUDA.
7. Read the acceleration report to see which attention, norm, and linear replacements actually happened.

## Environment and Pixi isolation

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: ltx_distillation` | Command is not running inside the LTX/Pixi environment or local LTX packages were not installed. | Run from the LTX-2 workspace with `pixi run ...`, or activate an environment where the LTX packages are installed. |
| Core TurboDiffusion imports work, but LTX imports fail | User mixed the core Wan environment with the TurboT2AV environment. | Keep the LTX Pixi environment separate. Reinstall local LTX packages in the LTX workspace rather than adding LTX deps into the Wan environment. |
| `Unable to import TurboDiffusion acceleration symbol ...` | TurboT2AV acceleration cannot see TurboDiffusion source/package imports. | Install TurboDiffusion into the LTX environment or add source-layout `PYTHONPATH` entries for the TurboDiffusion project and source package. |
| CUDA version or PyTorch wheel mismatch | Environment was solved or modified outside the tested Pixi task set. | Use the LTX Pixi workspace task set that pins CUDA 12.8 PyTorch, or rebuild a clean equivalent environment. |
| Pixi install is slow or compiles many CUDA packages | Expected for acceleration packages. | Treat installation as a setup step outside this skill's command renderer. The renderer only prints inference commands. |

## Hugging Face / Gemma gated access

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Downloading Gemma returns 401/403 or asks for authentication | Gemma is gated and the user has not accepted terms or has no authorized token. | Visit the model page, accept access terms, log in with a token that has access, and download the Gemma directory. Do not place the token in command logs or generated scripts. |
| Runtime cannot find tokenizer/model files under the Gemma path | `TURBO_GEMMA_PATH` points to the wrong directory level or an incomplete download. | Point `TURBO_GEMMA_PATH` at the directory that contains the local Gemma model files. Redownload outside this skill if necessary. |
| User has no Gemma HF token | The base LTX/Gemma text encoder assets cannot be acquired from the gated source. | Do not suggest bypassing gated access. Ask the user to obtain approved access or use an already-downloaded local Gemma directory supplied by an authorized source. |
| User asks to put `HF_TOKEN=...` into the rendered command | Credential leakage risk. | Keep tokens out of generated commands. Use token only for separate download/login steps. |

## Missing checkpoints and config paths

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `--student_checkpoint is required for --model_kind student` | Student run omitted the TurboT2AV checkpoint. | Supply the TurboT2AV student `model.pth` or FSDP-style checkpoint directory. |
| Config still points to placeholder checkpoint paths | Environment variables were not set or were overridden incorrectly. | Set `TURBO_CHECKPOINT_PATH` and `TURBO_GEMMA_PATH`; the runner uses these to override matching config keys. |
| File-not-found for LTX base checkpoint | `TURBO_CHECKPOINT_PATH` points to a missing file or wrong asset. | Use the LTX-2 base safetensors checkpoint expected by the config. |
| File-not-found for student checkpoint | `--student_checkpoint` points to an incomplete TurboT2AV download or wrong subdirectory. | Point directly to the student checkpoint file, or to a valid FSDP directory containing `sharded/` and `metadata.pth`. |
| Output directory is wrong or samples are skipped | Existing decoded MP4/WAV files are present and `--overwrite` was not used. | Choose a fresh output directory or pass `--overwrite` deliberately. |

## Prompt loading issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Fewer prompts than expected | `--num_prompts` was set, blank lines were removed, or only one shard is selected. | Remove or adjust `--num_prompts`; check `--num_shards`/`--shard_id`; inspect the `prompts_shard_XX.txt` file in the output directory. |
| CSV prompt column is ignored | Header does not contain `prompt`, `caption`, or `text`. | Rename the relevant column or use one prompt per line. |
| A comma-containing line is not split into columns | Headerless CSV-like input is intentionally treated as one prompt per line. | Add a recognized CSV header if structured CSV parsing is desired. |

## SageAttention, SpargeAttn, SageSLA, and TileLang

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Import error for `sageattention` | SageAttention was not installed in the LTX environment. | Run the acceleration install task in the LTX workspace or switch to `--attention_type default` for a dense fallback. |
| SageSLA/SLA construction asserts or imports fail | SpargeAttn/SLA dependency or TurboDiffusion acceleration imports are missing. | Install acceleration deps in the LTX environment and ensure TurboDiffusion source/package imports are visible. Use `--attention_type default` or `sageattn` for diagnosis. |
| TileLang import or TVM FFI runtime error | TileLang or the pinned TVM FFI package is missing/incompatible. | Reinstall the TileLang acceleration task in a clean LTX environment. For a controlled fallback, use `--quant_linear_backend turbodiffusion` or disable `--quant_linear`. |
| Build fails on H20/sm90-related kernels | CUDA arch-specific build settings or package patches were not applied. | Use the LTX acceleration install task that applies the build compatibility patches. Do not manually mix unpatched package versions unless debugging. |
| Build exhausts memory or CPU | Parallel CUDA builds are too aggressive. | Reduce build parallelism for the acceleration package outside runtime commands. |
| Acceleration report shows `replaced_attention=0` or many skipped modules | Scope/backend does not match model modules, or imports failed before replacement. | Check `--attention_scope`; start with `--attention_type default`, then `sageattn`, then `sagesla` after dependencies work. |

## `topk=0.3` and quality/speed trade-offs

| Issue | Guidance |
| --- | --- |
| User asks if `topk=0.3` is exact | It is not exact dense attention. It is the public speed/quality setting for the H20 benchmark and should be revalidated for new resolutions/prompts/checkpoints. |
| User sets `--sla_topk 0` | Invalid; accepted values are in `(0, 1]`. Use `0.3` for the public setting or `1.0` for quality-first sparse behavior. |
| User wants per-layer tuning | Use `--sla_topk_schedule START-END:TOPK,...`; invalid ranges and values are rejected. |
| Output quality drops on another GPU or resolution | Increase top-k, disable `--trim_text_context`, or compare against `--attention_type default` to isolate the source. |

## `trim_text_context`

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| User expected trimming by default | It is disabled unless explicitly requested. | Add `--trim_text_context` for the public fast student path. |
| Text-context shape changes surprise downstream code | Padding tokens are removed and attention mask becomes unnecessary. | Disable trimming for debugging or custom text encoder integrations. |
| Quality/regression concern | Trimming should be benchmarked with the target prompts and text encoder setup. | Compare a small prompt set with and without `--trim_text_context`. |

## FastNorm

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| FastNorm import fails | TurboDiffusion fused norm modules or Triton kernels are not importable. | Ensure TurboDiffusion acceleration imports are visible in the LTX environment; otherwise disable `--fast_norm`. |
| Some operations fall back to native norm | Unsupported shape, dtype, contiguity, or runtime error. | This can be expected. Use the acceleration report and timings to decide whether the flag helps. |
| Numeric differences appear | Fused kernels can change floating-point details. | Compare with `--fast_norm` disabled for sensitive experiments. |

## Quant linear backend semantics

| User question or symptom | Correct response |
| --- | --- |
| "Does TurboDiffusion `quant_linear` mean the same thing in TurboT2AV?" | No. Both replace Linear modules for W8A8-style inference, but TurboT2AV's recommended backend is `tilelang_postscale`, tuned for LTX/H20 shapes, and it is not a checkpoint-compression feature. |
| `tilelang_postscale` is slower than BF16 on a different GPU | The public recommendation was measured on H20. Rebenchmark `tilelang_postscale`, `turbodiffusion`, and dense BF16 on the target hardware. |
| User wants smallest checkpoint files | `--quant_linear` does not primarily compress checkpoints here; the integration retains BF16 fallback copies for unsupported shapes. |
| Original TurboDiffusion W8A8 backend import fails | It needs TurboDiffusion CUDA extension imports. | Use `tilelang_postscale` if installed, fix TurboDiffusion ops imports, or disable quant linear. |

## H20 benchmark vs other GPUs

The published `5.8505s` accelerated student result is not a universal promise. It depends on H20 hardware, CUDA/PyTorch/TileLang/SageAttention/SpargeAttn versions, output resolution, frame count, prompt count, and whether timing is generator-only or includes decode. For other GPUs:

- confirm the CUDA architecture supported by acceleration packages;
- expect first-sample JIT/autotune overhead unless warmed up;
- use `--warmup_samples` and `--timing_json` for controlled measurement;
- compare dense, W8A8/FastNorm, and SageSLA settings on the same prompt set;
- keep quality comparisons paired by prompt and seed.

## CUDA and memory

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `RuntimeError: CUDA is required` | Real AV generation was launched on a CPU-only environment. | Use a CUDA-capable machine. Help/command rendering can be CPU-only, but generation cannot. |
| Out-of-memory at `1024x1792` | The public resolution is large and was measured on H20-class hardware. | Lower `--video_height`, `--video_width`, prompt count, or shards; use `--skip_decode` only for generator timing. |
| First sample is much slower | JIT/autotune/model initialization overhead. | Use `--warmup_samples` and inspect `--timing_json`. |

## Multi-shard locking

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Shards appear to wait during startup | Default model-init lock serializes heavy model initialization. | This is expected. Use `--init_lock_path` to choose a lock or `--no_init_lock` only if concurrent initialization is safe. |
| Lock path permission error | Default lock directory is not writable. | Set `AV_EVAL_INIT_LOCK_DIR` to a writable directory or pass `--init_lock_path`. |
