# Core Components Troubleshooting

Use this reference for failures involving imports, model-component construction, VAE encode/decode, schedulers, and distributed helpers. Generation launchers, dataset schemas, and training command flags have their own sub-skills.

## Fast triage

1. Run the bundled smoke script with the same Python environment and package root the user will use:

   ```bash
   python skills/disco/pyramid-flow/sub-skills/core-components/scripts/smoke_core_components.py --package-root PATH_TO_PYRAMID_FLOW
   ```

2. If imports fail, fix dependency/package-root issues before debugging API shapes.
3. If imports pass but scheduler/VAE smokes fail, inspect version drift and tensor shape/device invariants.
4. If component smokes pass but generation/training fails, route to `generation-inference` or `training-workflows` for workflow-specific checks.

## Import and version problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: pyramid_dit`, `video_vae`, `diffusion_schedulers`, or `trainer_misc` | Pyramid-Flow source/import root is not visible to Python. The inspected repo has no package metadata, so a normal `pip install` may not have occurred. | Run from a checkout/package root, set `PYTHONPATH`, or pass `--package-root PATH_TO_PYRAMID_FLOW` to bundled scripts. Avoid hard-coding a machine-specific path into reusable code. |
| `ModuleNotFoundError: utils` while importing `video_vae` | `video_vae` imports the top-level `utils.py`; only adding the `video_vae/` directory is insufficient. | Put the repository/package root on `sys.path`, not just a subdirectory. |
| Missing `torch`, `diffusers`, `transformers`, `safetensors`, or `tokenizers` | Runtime dependencies not installed in the active environment. | Install the repo's declared runtime requirements or a compatible narrowed set. Keep `torch`/`torchvision` CUDA build alignment consistent. |
| `ImportError` or `AttributeError` inside diffusers/modeling classes | Version drift between repository-era APIs and installed `diffusers`/`torch`/`transformers`. | Compare against known facts: repository docs recommended Python 3.8.10, PyTorch 2.1.2, `transformers==4.39.3`, `accelerate==0.30.0`, and `diffusers>=0.30.1`; live inspection succeeded with newer `torch`/`diffusers` but that does not guarantee all generation/training paths. Try the documented baseline if component APIs break. |
| `No package metadata was found for spacy` | Some declared dependencies are not installed or are not needed for the current import-only workflow. | Do not install broad extras solely for core-component inspection. Install only when a selected workflow imports or uses that package. |
| Tokenizer or text encoder import failures | Incompatible `transformers`, `tokenizers`, `sentencepiece`, `tiktoken`, or missing checkpoint tokenizer files. | Verify package versions and checkpoint directory contents. For full generation, route to `generation-inference`. |

## CUDA and device problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `torch.cuda.is_available()` is false | CPU-only PyTorch build, missing driver/runtime visibility, or container did not expose GPUs. | Install a CUDA-capable PyTorch build matching the host driver and expose GPUs to the process. Component scheduler and tiny VAE smokes can still run on CPU, but generation/training are not truthfully covered. |
| `RuntimeError: Found no NVIDIA driver` or CUDA initialization errors | Driver/runtime mismatch or process isolation. | Confirm driver visibility with a host GPU probe and ensure the Python environment uses a compatible CUDA wheel/build. |
| CUDA OOM during generation or VAE decode | Model/checkpoint is too large for available GPU memory; VAE decode tile/window sizes are too large. | Use `model.enable_sequential_cpu_offload()` or `cpu_offloading=True`; set `save_memory=True`; enable VAE tiling. Route generation recipes to `generation-inference`. |
| Mixed CPU/CUDA tensor error | Latents, model output, text embeddings, scheduler tensors, or VAE are on different devices. | Move model components and input tensors consistently. For scheduler, call `set_timesteps(..., device=sample.device)` before stepping. |
| dtype mismatch with bf16/fp16 | `model_dtype`, autocast dtype, and checkpoint weights do not agree. | Prefer README's `model_dtype='bf16'` for public generation snippets unless the checkpoint explicitly supports another dtype. Use fp32 for CPU smokes. |

## Scheduler errors

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `KeyError: 3` or similar from `set_timesteps()` | `stage_index` is outside the scheduler's configured stage keys. Default `stages=3` has valid indexes `0`, `1`, `2`. | Validate `0 <= stage_index < scheduler.config.stages`. The bundled smoke script's negative case wraps this into a clearer message. |
| `IndexError` or missing stage schedule | `stage_range` length does not equal `stages + 1`, or custom stage configuration is inconsistent. | Use a monotonic `stage_range` covering `[0, 1]`, with one more boundary than the number of stages. |
| `ValueError` about integer timestep indexes in `step()` | Passing loop index from `enumerate(scheduler.timesteps)` instead of an actual timestep tensor/value. | Pass `t` from `for t in scheduler.timesteps`, not the integer index. |
| Output shape mismatch or broadcasting failure | `model_output` and `sample` shapes differ or have incompatible device/dtype. | Assert `model_output.shape == sample.shape` before `step()`, and keep tensors on the same device. |
| `step_index` or sigma index problems | `set_timesteps()` was not called for the current stage before `step()`, or `step()` called too many times for the schedule length. | Call `set_timesteps(num_inference_steps, stage_index, device=...)` once per stage and step exactly over `scheduler.timesteps`. |
| Unexpected noisy/unstable samples | `gamma`, `shift`, or stage schedule changed from checkpoint training assumptions. | Prefer wrapper defaults unless reproducing a known training configuration. |

## VAE encode/decode and round-trip problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Decoded image/video has different H/W than input | Input spatial size was not divisible by the VAE downsample scale (`8` by default). The model may round through conv/downsample operations instead of failing early. | Precheck `height % 8 == 0` and `width % 8 == 0`. The bundled smoke script's negative case raises a clear `ValueError` for non-divisible sizes before calling the model. |
| Assertion in `chunk_encode`: `(num_frames - 1) % downsample_scale == 0` | `temporal_chunk=True` with an incompatible frame count. | Use frame counts that satisfy the temporal chunk invariant, or disable temporal chunking for tiny tests. |
| `AttributeError: 'tuple' object has no attribute 'latent_dist'` | `return_dict=False` was passed to `encode()`, so the posterior is returned in a tuple. | Use `return_dict=True` or unpack the tuple explicitly. |
| `AttributeError: 'tuple' object has no attribute 'sample'` | `return_dict=False` was passed to `decode()`. | Use `return_dict=True` or unpack the tuple. |
| `GroupNorm` or channel divisibility error when creating a tiny VAE | Reduced channel config is incompatible with `encoder_norm_num_groups` or `decoder_norm_num_groups`. | Keep each block channel count divisible by the group count. The bundled tiny smoke uses channels `(8, 8, 8, 8)` with group count `4`. |
| `RuntimeError` from 4D vs 5D tensor rank | Direct `CausalVideoVAE.encode()` expects `[B, C, T, H, W]`; only wrapper helpers convert 4D images to one-frame videos. | Unsqueeze a time dimension for direct VAE calls: `x = x.unsqueeze(2)`. |
| Reconstruction wrapper returns no training loss | `CausalVideoVAELossWrapper(load_loss_module=False)` leaves `self.loss=None`. | Use the wrapper only for encode/decode/reconstruct helpers, or construct with `load_loss_module=True` and provide needed loss dependencies/checkpoints for training. |
| LPIPS/discriminator checkpoint error | VAE loss training needs an LPIPS checkpoint path when loading the loss module. | Provide `lpips_ckpt` according to the VAE training workflow; route training setup to `training-workflows`. |
| Slow or memory-heavy VAE smoke | Instantiating the default VAE is large. | Use the bundled script's reduced-channel tiny VAE or run with `--skip-tiny-vae` for import/scheduler-only diagnostics. |

## Invalid model path or variant

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `OSError`, `FileNotFoundError`, or Hugging Face `from_pretrained` errors during wrapper construction | `model_path` does not contain the expected checkpoint subdirectories. | Confirm `model_path/model_variant` exists for the DiT and `model_path/causal_video_vae` exists when `load_vae=True`. |
| `NotImplementedError: Unsupported DiT architecture` | `model_name` is not `pyramid_flux` or `pyramid_mmdit`. | Correct `model_name` or route to generation-inference for variant/checkpoint selection guidance. |
| `NotImplementedError: Unsupported Text Encoder architecture` | Same architecture mismatch for text encoder selection. | Keep `model_name` aligned with the checkpoint family. |
| VAE scale/shift mismatch or strange colors | Using `pyramid_flux` constants with MMDiT checkpoint or vice versa. | Ensure `model_name`, `model_variant`, and checkpoint repository are aligned. |
| 384p/768p output shape or OOM mismatch | Variant resolution does not match requested `height`, `width`, or `temp`. | Use generation-inference workflow guidance for public 384p/768p settings. Core invariant: height/width should be divisible by 8. |
| Wrapper construction downloads or touches large artifacts unexpectedly | `from_pretrained` is resolving remote/local model files. | Do not construct the full wrapper for lightweight API inspection. Use signature docs or pass `load_text_encoder=False`/`load_vae=False` only when source code path still does not require checkpoint files for the selected component. |

## Distributed helper problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Not using distributed mode` printed | No `RANK`/`WORLD_SIZE`/`LOCAL_RANK` or OpenMPI variables were present. | This is expected for single-process component inspection. Use torchrun/OpenMPI launchers only for multi-GPU workflows. |
| Assertion: `The pytorch distributed should be initialized` | `init_sequence_parallel_group()` or `init_sync_input_group()` was called before DDP initialization. | Call `init_distributed_mode()` under a proper launcher, or skip sequence/sync groups in single-process code. |
| Assertion: `sequence parallel group is already initialized` | Reinitializing global sequence-parallel state in the same process. | Initialize once per process. Restart the process for a clean group configuration. |
| Assertion: `The process needs to be evenly divided` | `sp_proc_num` is not divisible by `sp_group_size`. | Adjust launcher world size or sequence-parallel group size. |
| Accessor assertion: `sequence parallel group is not initialized` | Calling `get_sequence_parallel_group()` without initialization. | Guard with `is_sequence_parallel_initialized()`. |
| Non-master logs missing | `setup_for_distributed()` suppresses builtin `print` on non-master ranks. | Use `print(..., force=True)` in distributed-aware debugging code. |

## Recommended diagnostic order

1. **Import-only**: `smoke_core_components.py --skip-tiny-vae` to confirm package root and basic dependencies.
2. **Scheduler math**: default smoke checks both schedulers on CPU with synthetic tensors.
3. **Tiny VAE**: default smoke checks a reduced-channel VAE round trip; disable only when diagnosing imports.
4. **Negative cases**: `--check-negative-cases` confirms clear handling for out-of-range scheduler stage and non-divisible VAE input shape.
5. **Workflow-specific escalation**: if core smokes pass, use the generation, data-preparation, or training sub-skill for checkpoint, dataset, launcher, and long-running backend issues.
