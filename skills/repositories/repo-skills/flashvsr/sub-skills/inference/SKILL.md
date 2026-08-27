---
name: inference
description: "Routes official FlashVSR v1 and v1.1 GPU inference across full,
  tiny, and tiny-long pipelines, including aligned input preparation, LCSA
  controls, VRAM recovery, and MP4 output."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# FlashVSR Inference

Use this sub-skill for official DiffSynth Studio FlashVSR inference on an NVIDIA
GPU. It covers v1 and v1.1, image-sequence directories and videos, the full,
tiny, and tiny-long routes, and one-step streaming calls. Do not use it for
training, unrelated DiffSynth pipelines, community integrations, or obtaining
model credentials.

## Route First

1. Prefer **v1.1** for its documented stability and fidelity improvements. Use
   **v1** only when reproducing v1 weights/results. Never mix a version's DiT,
   LQ projection, or decoder checkpoint with the other version.
2. Select a pipeline:
   - **full** (`FlashVSRFullPipeline`): reference Wan VAE decoder route,
     highest VRAM pressure; decoder tiling is available.
   - **tiny** (`FlashVSRTinyPipeline`): tiny conditional decoder for ordinary
     clips; lower decoder cost than full.
   - **tiny-long** (`FlashVSRTinyLongPipeline`): keeps prepared input on CPU,
     moves stream slices to CUDA, decodes each stream chunk, and accumulates
     output on CPU. Choose it first for long clips or as a memory fallback.
3. Read [workflows.md](references/workflows.md) for the version/route model
   contracts and complete recipes. Read
   [api-reference.md](references/api-reference.md) before changing defaults.
4. Validate inputs before allocating models:

   ```bash
   python <skill-root>/sub-skills/inference/scripts/validate_input.py INPUT --json
   ```

   Use `--geometry-mode prepared` to reject an already-prepared tensor geometry
   that is not divisible by 128. Use `--frame-policy preserve-all` when the
   output must retain every real source frame.
5. If import, CUDA, memory, geometry, color, or MP4 writing fails, use
   [troubleshooting.md](references/troubleshooting.md).

## Non-Negotiable Streaming Contract

- FlashVSR is optimized for **4x** restoration. Bicubic-upscale the low-quality
  source by 4, then center-crop down to height and width divisible by **128**.
  Pass those exact target dimensions to both `LQ_video` and `height`/`width`.
- Prepare RGB as `torch.bfloat16` in `[-1, 1]` with shape
  **`[1, 3, F, H, W]`**.
- The official frame preparation appends/repeats the final frame and selects
  **`F = 8n+1`**. The expected returned clip has **`F-4 = 8n-3`** frames. At
  least 21 real frames are required by the verified recipe (`F >= 25`). The
  pipeline's internal `num_frames % 4 == 1` adjustment is weaker and does not
  establish the required streaming layout.
- Initialize the cross-attention cache exactly once before calls. For a runtime
  independent of any checkout layout, load the positive context tensor from an
  application-owned asset and call
  `pipe.init_cross_kv(context_tensor=context)`. The verified canonical context
  tensor is bfloat16 with shape `[1, 512, 4096]`.
- Use the official one-step settings:
  `cfg_scale=1.0`, `num_inference_steps=1`, `if_buffer=True`,
  `is_full_block=False`, `kv_ratio=3.0`, and `color_fix=True` initially.
- Let `sparse_ratio` be 1.5 (faster) or 2.0 (more stable), then pass
  `topk_ratio = sparse_ratio * 768 * 1280 / (H * W)`. Start with
  `local_range=11` for stability or 9 for sharper detail.
- A successful pipeline call returns **`[3, F-4, H, W]`** in approximately
  `[-1, 1]`. Convert to `[T, H, W, 3]` uint8 and encode at the source FPS.

## Backend Gate

The Wan DiT module imports `block_sparse_attn` unconditionally, and official
LCSA calls the extension. `is_full_block=True` does not implement a dense
fallback in the verified stream path. Do not begin expensive inference until
this succeeds in the target environment:

```bash
python -c "from block_sparse_attn import block_sparse_attn_func; print('LCSA import OK')"
```

The prepared target profile is Python 3.11, PyTorch 2.6.0+cu124, CUDA 12.4,
and A100 SM80. The extension import gate and a small bf16 streaming-attention
kernel smoke test passed on that profile. This does not prove real checkpoint
loading or FlashVSR inference.

## Evidence and Verification Boundary

This operating guidance was distilled from the public FlashVSR README,
three pipeline implementations, Wan video DiT attention and VRAM-management
code, and all six official v1/v1.1 inference recipes. The bundled validator is
the only executable in this skill and is read-only; it performs no model or
dataset acquisition.

Static contracts and synthetic geometry/frame planning are covered. Native
CUDA candidates remain deferred: import and execution of the block-sparse
backend, loading matching v1/v1.1 weights, full/tiny/tiny-long GPU smoke
inference, CUDA-OOM recovery, and reopening a produced H.264 MP4. Do not claim
those candidates passed until they are run with the selected weights and GPU.

## Verification Candidates

- **Synthetic invalid geometry:** run the validator in `prepared` mode with a
  positive frame count and one dimension such as 1279; it must exit non-zero
  and report the 128-alignment error without allocating a model.
- **Synthetic long-video fallback:** run the metadata fixture with a valid
  128-aligned source geometry and a large frame count using
  `--frame-policy preserve-all`; confirm it reports the `8n+1` input, output
  tail trim, and the need to segment before host-memory exhaustion. This is a
  planning test, not a claim that tiny-long GPU inference completed.
