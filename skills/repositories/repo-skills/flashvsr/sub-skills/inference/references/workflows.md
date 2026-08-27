# FlashVSR v1/v1.1 Inference Workflows

Read this for model-file contracts, route selection, input preparation, the
one-step call, long-video behavior, and MP4 writing. These recipes intentionally use generic application-owned paths/modules and do
not require the source repository checkout.

## Choose Version and Route

| Need | Version/route | Why | Main trade-off |
|---|---|---|---|
| Full decoder when memory allows | v1.1 full | v1.1 is documented as more stable and faithful; full uses Wan VAE decode | highest VRAM and decode cost |
| Faster/lighter ordinary clip | v1.1 tiny | tiny conditional decoder | different decoder; full-route parity is not implied |
| Long clip or OOM recovery | v1.1 tiny-long | LQ stays on CPU, stream slices move to GPU, decoded chunks return to CPU | host RAM/output concatenation still grow with duration |
| Exact initial-release reproduction | matching v1 route | preserves v1 weights and buffered LQ projection | older stability/fidelity behavior |

v1 and v1.1 use the same three pipeline classes and call parameters. The
verified inference-script differences are the model directory, output name,
and LQ projection implementation:

| Version | LQ projection | Weight family |
|---|---|---|
| v1 | `Buffer_LQ4x_Proj` | all files from one v1 directory |
| v1.1 | `Causal_LQ4x_Proj` | all files from one v1.1 directory |

Do not infer any other version-specific API change, and do not mix files across
rows.

## Model and Runtime Asset Contracts

Set one application-owned `MODEL_DIR` for the selected version. Model acquisition
and credentials are outside this sub-skill.

| Asset | full | tiny | tiny-long | Load contract |
|---|---:|---:|---:|---|
| `diffusion_pytorch_model_streaming_dmd.safetensors` | required | required | required | load through `ModelManager` as the Wan DiT |
| `Wan2.1_VAE.pth` | required | not used | not used | load through `ModelManager` for full decode |
| `LQ_proj_in.ckpt` | required | required | required | strict state-dict load into the version-matched LQ projection |
| `TCDecoder.ckpt` | not used | required | required | state-dict load with `strict=False`; inspect missing/unexpected keys |
| positive context tensor | required | required | required | application-owned tensor, canonical shape `[1,512,4096]`, passed to `init_cross_kv(context_tensor=...)` |

The LQ projection classes and tiny decoder builder are official runtime support
components but are not public exports of the verified DiffSynth package. A
checkout-independent deployment must package their implementation in its own
runtime module. Treat this as a required application integration step; do not
leave imports pointing at an examples or checkout-relative `utils` package.

Before loading large checkpoints, assert all required files are readable and
run the LCSA import gate:

```bash
python -c "from block_sparse_attn import block_sparse_attn_func; print('LCSA import OK')"
```

An import failure is blocking; `is_full_block=True` is not a fallback.

## Prepare Image-Directory or Video Input

Run the bundled read-only validator first:

```bash
# Natural-sort and validate a PNG/JPEG frame directory.
python <skill-root>/sub-skills/inference/scripts/validate_input.py frames_dir

# Inspect video geometry, frame count, and FPS.
python <skill-root>/sub-skills/inference/scripts/validate_input.py input.mp4 --json

# Plan repeat-padding so every source frame can be retained after trimming.
python <skill-root>/sub-skills/inference/scripts/validate_input.py input.mp4 --frame-policy preserve-all
```

### Spatial preparation

For every source frame `(w0,h0)`:

1. Decode/convert to RGB. For image directories, natural-sort names so `2`
   precedes `10`; every frame must have identical geometry.
2. Strongly prefer `scale=4`. Compute
   `scaled_w=round(w0*scale)`, `scaled_h=round(h0*scale)`.
3. Compute target geometry by flooring each scaled dimension:
   `W=(scaled_w//128)*128`, `H=(scaled_h//128)*128`. Reject if either is zero.
4. Bicubic-resize to `(scaled_w,scaled_h)`, then center-crop to `(W,H)`.
5. Convert uint8 RGB to `CHW` bfloat16 with `x/255*2-1`.
6. Stack as `[1,3,F,H,W]`.

The model returns the prepared `H x W` geometry; it does not apply another 4x
increase. The 4x output claim is relative to the original source before the
bicubic preparation.

Do not pass an unaligned source tensor and rely on pipeline rounding. The full
route does not call the generic resize check; tiny routes only round scalar
`height`/`width` to a multiple of 16 and do not resize `LQ_video`, creating a
shape mismatch.

### Temporal preparation

The official floor policy for `T` real frames is:

```text
n = floor((T + 3) / 8)
O = 8n - 3                # model output frames; O <= T
F = O + 4 = 8n + 1        # LQ_video frames passed to the pipeline
```

Build the input index list as all real indices plus four repeats of the final
index, then truncate it to `F`. This can drop trailing source frames when `F<T`
and always produces `O=F-4` output frames. Require `O>=21` (`F>=25`).

To preserve every source frame, choose the next valid output length instead:

```text
n = ceil((T + 3) / 8)
O = 8n - 3                # O >= T
F = O + 4
```

Repeat the final source frame until `F`, run inference, and trim the final
`O-T` output frames. This is a deliberate preservation adaptation; the official
sample policy uses the floor formula.

Image directories default to 30 FPS. For video, preserve a valid reported FPS;
if metadata is absent, use an explicit application policy such as 30 FPS.

## Initialize Pipelines

The following snippets specify the wiring contract. `ProjectionClass` and
`build_tcdecoder` must come from the application's packaged official runtime
support module, not a source-checkout utility.

### Shared DiT and LQ projection

```python
from pathlib import Path
import torch
from diffsynth import ModelManager

model_dir = Path(MODEL_DIR)
mm = ModelManager(torch_dtype=torch.bfloat16, device="cpu")
mm.load_models([str(model_dir / "diffusion_pytorch_model_streaming_dmd.safetensors")])

pipe = PipelineClass.from_model_manager(mm, device="cuda")
projection = ProjectionClass(in_dim=3, out_dim=1536, layer_num=1).to(
    "cuda", dtype=torch.bfloat16
)
lq_state = torch.load(model_dir / "LQ_proj_in.ckpt",
                      map_location="cpu", weights_only=True)
projection.load_state_dict(lq_state, strict=True)
pipe.denoising_model().LQ_proj_in = projection
```

Choose `ProjectionClass=Buffer_LQ4x_Proj` for v1 or
`ProjectionClass=Causal_LQ4x_Proj` for v1.1.

### Full additions

Load both models before creating `FlashVSRFullPipeline`:

```python
mm.load_models([str(model_dir / "Wan2.1_VAE.pth")])
pipe = FlashVSRFullPipeline.from_model_manager(mm, device="cuda")
# Inject the version-matched projection after constructing this final pipe.

# Decode-only memory reduction; omit if this VAE must encode later.
pipe.vae.model.encoder = None
pipe.vae.model.conv1 = None
```

The full route's model manager must resolve both `wan_video_dit` and
`wan_video_vae`; stop if either is `None`.

### Tiny and tiny-long additions

After creating `FlashVSRTinyPipeline` or `FlashVSRTinyLongPipeline` and
injecting the projection:

```python
pipe.TCDecoder = build_tcdecoder(
    new_channels=[512, 256, 128, 128],
    new_latent_channels=16 + 768,
)
tc_state = torch.load(model_dir / "TCDecoder.ckpt",
                      map_location="cpu", weights_only=True)
load_result = pipe.TCDecoder.load_state_dict(tc_state, strict=False)
print(load_result)  # Review missing/unexpected keys; do not suppress the result.
```

### Final shared initialization

```python
pipe.to("cuda")
pipe.enable_vram_management(num_persistent_param_in_dit=None)

context = torch.load(POSITIVE_CONTEXT_PATH,
                     map_location="cpu", weights_only=True)
assert tuple(context.shape) == (1, 512, 4096)
pipe.init_cross_kv(context_tensor=context)
pipe.load_models_to_device(["dit", "vae"])
```

For tiny routes, `vae` may be absent and is skipped. The explicit context avoids
the pipeline's hard-coded relative-path default.

## One-Step Streaming Call

For each independently prepared clip, clear stale allocator blocks between
calls if needed and invoke:

```python
sparse_ratio = 2.0  # 1.5 faster; 2.0 more stable
video = pipe(
    prompt="",
    negative_prompt="",
    cfg_scale=1.0,
    num_inference_steps=1,
    seed=0,
    tiled=False,  # full only: set True when decode VRAM is the bottleneck
    LQ_video=LQ,
    num_frames=F,
    height=H,
    width=W,
    is_full_block=False,
    if_buffer=True,
    topk_ratio=sparse_ratio * 768 * 1280 / (H * W),
    kv_ratio=3.0,
    local_range=11,
    color_fix=True,
)
assert tuple(video.shape) == (3, F - 4, H, W)
```

The stream mode is internal and always enabled by these pipeline calls. Do not
call the internal model wrapper directly. The first iteration initializes K/V
caches from six latent-time positions; subsequent iterations process two and
reuse bounded cache history.

### Parameter decisions

| Decision | Start with | Change when |
|---|---|---|
| `sparse_ratio` | 2.0 | use 1.5 for speed after quality comparison; it changes `topk_ratio`, not a direct pipeline argument |
| `topk_ratio` | baseline-normalized formula above | recompute for every target geometry; do not keep 2.0 at arbitrary resolution |
| `kv_ratio` | 3.0 | do not tune without quality/runtime evidence; stream code truncates it to an integer |
| `local_range` | 11 | use 9 for sharper details if stability is acceptable |
| `color_fix` | true | compare false when colors shift or correction is silently skipped |
| `tiled` | false on full when memory permits | true on full for lower decoder VRAM; tiny routes do not use these VAE tile controls |
| `is_full_block` | false | never use it as a missing-extension workaround; current stream source does not branch on it |
| `if_buffer` | true | keep true for official stream geometry |

## Long-Video Behavior and Memory Ladder

Tiny-long differs from tiny in three observable ways:

1. Prepared `LQ_video` remains on CPU.
2. Each LQ slice is transferred to CUDA immediately before projection/decoder
   use.
3. Each decoded chunk is moved back to CPU; all chunks are concatenated at the
   end.

This reduces sustained GPU frame/decoder memory but is not unbounded streaming:
the complete prepared input and output still consume host RAM. For very long or
high-resolution clips, estimate host memory before tensor construction and
segment the video into valid `8n+1` windows. Repeat enough boundary frames for
context, discard repeated/overlap output deterministically, and encode segments
incrementally instead of retaining the whole result.

Use this recovery order for CUDA OOM:

1. Retry the same clip with tiny-long.
2. On full only, set `tiled=True` and keep overlapping default tile geometry.
3. Reduce target spatial geometry while retaining 128 alignment; spatial area
   dominates attention cost.
4. Use `sparse_ratio=1.5` after checking quality.
5. Process one clip/segment at a time; release tensors and clear CUDA cache
   between clips.
6. If host RAM becomes the failure instead, segment before creating the full
   prepared tensor and write output incrementally.

## Write MP4 Output

```python
import imageio.v2 as imageio
import numpy as np

frames = video.permute(1, 2, 3, 0)  # T,H,W,C
frames = ((frames.float() + 1.0) * 127.5).clamp(0, 255)
frames = frames.to(torch.uint8).cpu().numpy()

with imageio.get_writer(
    str(output_path), fps=float(source_fps), quality=6, codec="libx264"
) as writer:
    for frame in frames:
        writer.append_data(np.asarray(frame))
```

Create the parent directory first, use an `.mp4` suffix, preserve source FPS,
and verify the written file's width, height, frame count, and FPS. Quality 6 is
the full/tiny recipe; the long example uses 5. If `libx264` is unavailable,
follow the codec recovery in [troubleshooting.md](troubleshooting.md) rather
than changing model output.
