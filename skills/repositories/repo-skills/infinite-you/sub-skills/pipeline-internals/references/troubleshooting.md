# Troubleshooting

## How to use this guide

If an import or signature check is failing, run the bundled signature helper first:

- `scripts/inspect_pipeline_signatures.py --help`
- `scripts/inspect_pipeline_signatures.py --json`

The goal is to separate API drift from model-file, hardware, and checkpoint problems before you edit runtime code.

## Common failure modes

| Symptom or message | Likely cause | Recovery step | Stop when |
| --- | --- | --- | --- |
| `KeyError: 'image_proj'`, missing keys, unexpected keys, or size mismatch while loading `image_proj_model.bin` | The checkpoint layout does not match the current `Resampler` constructor, or the file is from a different revision | Confirm that the checkpoint exposes an `image_proj` entry, compare its shapes with the current `image_proj_num_tokens`, `embedding_dim`, and `output_dim`, then select or rebuild a matching checkpoint | The model file is missing or belongs to a different model family that cannot be reconciled locally |
| `mat1 and mat2 shapes cannot be multiplied`, dtype mismatch, or `expected scalar type BFloat16` during projection | The identity embedding, Resampler, or downstream controlnet tensors are on different devices or dtypes | Keep the ArcFace embedding as a single 512-d vector, reshape it to `[1, 1, 512]`, and keep the projection path on CUDA bf16 before moving it back to CPU | You need CPU-only execution or a dtype that the current code path does not support |
| `No face detected in the input ID image` | The detector missed the face at all three scales, or the face is too small, blurred, occluded, or not visible enough | Use a clearer RGB portrait, crop the face larger, reduce occlusion/blur, or choose an image with a more frontal face | There is no detectable face in the image and you cannot change the input |
| `No face detected in the control image` | The control image does not contain a face that the detector can use for landmark drawing | Use a control image with a visible face, or provide no control image and let the pipeline use the black control canvas | You intentionally want pose or structure guidance without any face landmarks |
| The wrong person is selected in a multi-person image | The code always picks the largest detected face | Pre-crop the intended subject so it is the largest face in the frame, or use a single-subject portrait | You need a different face selection policy; that requires code changes |
| `.cuda()` failures, `device='cuda'` errors, or CPU-only fallback does not work | The pipeline hard-codes CUDA for ArcFace, face alignment, and identity projection | Do not treat `cpu_offload` as CPU-only mode. It only stages the Diffusers components. For CPU support, refactor the hard-coded CUDA moves and re-test | CUDA is unavailable and you are not changing the implementation |
| bf16 load or compute failures, especially on older GPUs | The source loads the main models and projection path with `torch.bfloat16` | Verify `torch.cuda.is_bf16_supported()` and the GPU generation. If bf16 is unsupported, you need an explicit fp16/fp32 rewrite of the affected code paths | You cannot provide bf16-capable hardware and are not changing the dtype strategy |
| Quantized weights behave oddly after offload or adapters stop loading | Quantization and offload were applied in the wrong order, or the wrong object was quantized | Keep the source order: quantize the relevant modules first, freeze them, assemble the Diffusers pipeline, then use CPU offload only at inference time | The installed `optimum.quanto` API no longer exposes the expected quantize/freeze behavior |
| `delete_adapters`, `load_lora_weights`, or `set_adapters` is missing or behaves differently | Diffusers API drift or version mismatch | Compare the bundled signature snapshot with the installed package, pin the documented Diffusers version, and verify that adapter names and weights lists have matching lengths | The library version is intentionally different and you are updating the adapter logic too |
| Optional LoRA effects stack unexpectedly or remain after switching modes | Previous adapters were not deleted before loading the new set | Delete the `realism` and `anti_blur` adapters before loading the new LoRA list, then call `set_adapters` only when the names and weights are aligned | The selected Diffusers build does not support the adapter methods used here |
| Missing `InfuseNetModel`, missing `transformer` / `text_encoder_2` subfolders, or an unexpected model download starts | The local model tree does not match the expected layout, or the fallback download path is being triggered | Verify the local `infu_flux_v1.0/<variant>/InfuseNetModel` layout and the base FLUX subfolders before changing code. If the base model is gated, authenticate and accept the license first | Model files or network access are unavailable and you are not changing the layout |
| InsightFace provider warnings or `onnxruntime` messages about the execution provider | `onnxruntime` does not expose the CUDA provider, or the provider list falls back to CPU | The source lists `CUDAExecutionProvider` first and `CPUExecutionProvider` second. CPU fallback may still allow face detection, but the rest of the pipeline still requires CUDA for ArcFace projection and model execution | You are intentionally redesigning the pipeline for CPU-only execution |
| `scheduler.set_timesteps` signature mismatch or custom timesteps/sigmas are rejected | Diffusers scheduler API drift | Use the bundled signature helper to compare the installed API, then update `retrieve_timesteps` and the scheduler call sites together | The scheduler class is intentionally different and the timestep logic must be rewritten |

## Practical recovery order

1. Check the signature helper output against this sub-skill.
2. Check the checkpoint layout and model-tree paths.
3. Check CUDA and bf16 support.
4. Check adapter and scheduler API compatibility.
5. Only then edit the pipeline code.
