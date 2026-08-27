# LoRA and adapter troubleshooting

Use this checklist when FLUX LoRA, composition, conversion, IP-Adapter, PuLID, or safetensor merge workflows fail in an installed `nunchaku` environment.

## Backend and package basics

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Import or extension loading fails before any LoRA code runs | Nunchaku was installed without a compatible Torch/CUDA stack or GPU architecture. | Confirm CUDA is available, the Nunchaku wheel/build matches the installed PyTorch CUDA version, and the transformer can load before adding adapters. |
| Pipeline builds but generation fails on CPU-only hosts | Quantized Nunchaku FLUX workflows require CUDA-backed extensions. | Use a CUDA host; CPU is not a full substitute for these workflows. |
| Model or adapter download fails | Hugging Face asset is private, gated, renamed, or network-restricted. | Pass a local safetensors path, set the appropriate Hugging Face credentials in the environment, or use `local_files_only`-style download controls where supported. |

## LoRA loading and strength

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| LoRA appears to have no effect | Wrong file, incompatible format, unsupported target model, or strength too low. | Verify the file is a FLUX transformer LoRA, load with `update_lora_params(...)`, and try a clear strength such as `1.0` on a short prompt. |
| `set_lora_strength` changes all styles at once | It is a global post-scale for the currently loaded LoRA branch. | For multiple LoRAs, recompute `compose_lora([(path, per_lora_strength), ...])` with the desired per-LoRA strengths. |
| Changing a single LoRA strength after composition does not work | Composition bakes each individual strength into the composed state dict. | Recompose from the original LoRA inputs with new strengths; keep the original Diffusers-format inputs available. |
| Composition raises an assertion about Nunchaku format | `compose_lora` expects Diffusers-compatible LoRA inputs. | Do not compose Nunchaku-format LoRAs. Recompose from original Diffusers/Kohya-style LoRAs, then convert afterward if needed. |
| Conversion takes a long time | LoRA conversion is single-threaded and may be slow for large files/ranks. | Pre-compose and pre-convert once with the CLI; reuse the saved output for future runs. |
| Inference slows down with many LoRAs | The composed rank is large, and Nunchaku keeps the LoRA branch separate from the main quantized branch. | Reduce the number/rank of active LoRAs, lower unnecessary strengths, or pre-convert only when the deployment needs a fixed artifact. |
| Qwen custom LoRA request appears related but fails | Custom Qwen LoRA support is documented as under development. | Do not apply these FLUX LoRA APIs to Qwen custom LoRAs. Use pre-quantized Qwen Lightning assets through the Qwen workflow instead. |

## Compose and convert CLIs

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `python -m nunchaku.lora.flux.compose` aborts on assertion | The number of `-i` paths and `-s` strengths differ. | Provide exactly one strength per input path, or use `scripts/compose_lora_cli.py` for clearer validation. |
| Output path parent does not exist | The caller chose a nested output path. | The package compose function creates the parent directory; for other tools, create it before saving. |
| Converted file name is unexpected | `convert` derives `svdq-fp4-*` or `svdq-int4-*` from the quant path when `--lora-name` is omitted. | Pass `--lora-name` explicitly if a stable deployment file name is required. |
| Converted LoRA works with one base but not another | Nunchaku-format LoRA conversion uses the selected quantized base state. | Convert against the same quantized base checkpoint family/precision used at inference time. |

## IP-Adapter

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| User requests new IP-Adapter development | Support is documented as deprecated in March 2026. | Warn the user and prefer maintaining existing workflows only, unless the user explicitly accepts the deprecation risk. |
| `apply_IPA_on_pipe` raises an unknown pipeline class error | The pipeline class name is not supported by the adapter dispatcher. | Use a compatible FLUX-style pipeline class whose name starts with `Flux` or `IPAFlux`; do not route arbitrary pipelines through this adapter. |
| Generation ignores the image prompt | Adapter weights were not loaded before patching, `ip_adapter_image` was omitted, or the reference image was not RGB. | Call `pipeline.load_ip_adapter(...)`, then `apply_IPA_on_pipe(...)`, then pass `ip_adapter_image=reference.convert("RGB")` to generation. |
| Shape or key errors while loading adapter weights | The `repo_id`, `weight_name`, or adapter version does not match the expected per-layer FLUX IP-Adapter layout. | Use the same repo for both Diffusers `load_ip_adapter(...)` and `apply_IPA_on_pipe(..., repo_id=...)`, and verify the safetensors file name. |
| Cache plus IP-Adapter behaves inconsistently | Cache and adapter helpers both mutate pipeline/transformer call paths. | Apply helpers in a known order, then rerun a small generation smoke. If diagnosing, disable cache first and confirm IP-Adapter alone. |

## PuLID

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Identity conditioning has no effect | `pulid_forward` was not bound to the transformer or `id_image` was omitted. | After constructing `PuLIDFluxPipeline`, run `pipeline.transformer.forward = MethodType(pulid_forward, pipeline.transformer)` and pass `id_image`. |
| PuLID initialization downloads or fails on face/vision assets | PuLID needs PuLID weights, EVA-CLIP, InsightFace AntelopeV2, FaceXLib parsing models, and ONNX runtime providers. | Pre-stage those assets in the runtime cache or pass local asset paths where the pipeline constructor supports them. |
| Face detection/alignment fails | The identity image has no clear face, too low resolution, unusual crop, or unsupported image mode. | Use a clear front-facing RGB image and convert with `.convert("RGB")`; try a different reference image before changing model code. |
| ONNX provider error | `onnx_provider="gpu"` requires CUDA ONNX Runtime support. | Install a compatible ONNX Runtime GPU package, or use the CPU provider if performance is acceptable and supported by the environment. |
| Identity is too weak or too strong | `id_weight` is not tuned for the prompt/reference pair. | Start near `1.0`, then reduce for subtler identity transfer or increase cautiously if the pipeline accepts it. |

## Merge safetensors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `merge_safetensors` cannot find expected files | The input is not a split quantized model layout. | Ensure the directory/repo contains `unquantized_layers.safetensors`, `transformer_blocks.safetensors`, `config.json`, and `comfy_config.json`, or pass the correct `subfolder`. |
| Metadata is wrong for the output model | Incorrect `model_class` argument. | Use the exact target class string, such as `NunchakuFluxTransformer2dModel` for FLUX packaging. |
| User expects LoRA composition from `merge_safetensors` | The utility merges split model safetensors, not LoRA adapters. | Use `compose_lora` for LoRA composition and `to_nunchaku`/`convert` for LoRA conversion. |

## Verification candidates

For later native verification, consider bounded runs derived from `tests/flux/test_flux_dev_loras.py`, `tests/flux/test_flux_dev_IPA.py`, and `tests/flux/test_flux_dev_pulid.py` when CUDA and assets are available. Treat them as candidates only; this troubleshooting guide does not claim any native test or example was run during drafting.
