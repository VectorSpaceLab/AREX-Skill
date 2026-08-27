# FlashVSR Inference API Reference

Read this when constructing a pipeline, changing a call parameter, reasoning
about LCSA/cache behavior, or checking tensor contracts. Signatures and behavior
below were verified from the FlashVSR pipeline/model implementation; expensive
GPU execution was not performed.

## Public Pipeline Surfaces

The installed DiffSynth module exports these classes:

| Route | Class | Decoder | Input placement in the official recipe |
|---|---|---|---|
| full | `FlashVSRFullPipeline` | Wan video VAE | prepared tensor on CUDA |
| tiny | `FlashVSRTinyPipeline` | tiny conditional decoder (`TCDecoder`) | prepared tensor on CUDA |
| tiny-long | `FlashVSRTinyLongPipeline` | chunked tiny conditional decoder | prepared tensor on CPU; slices move to CUDA |

All three expose these source signatures:

```python
Pipeline(device="cuda", torch_dtype=torch.float16)
Pipeline.from_model_manager(
    model_manager, torch_dtype=None, device=None, use_usp=False
)
pipe.enable_vram_management(num_persistent_param_in_dit=None)
pipe.init_cross_kv(context_tensor=None)
```

`from_model_manager` fetches `wan_video_dit`; full also fetches
`wan_video_vae`. Although `use_usp` is accepted, the implementation sets
`use_unified_sequence_parallel=False`.

Full exposes the Wan VAE helpers:

```python
pipe.encode_video(input_video, tiled=True,
                  tile_size=(34, 34), tile_stride=(18, 16))
pipe.decode_video(latents, tiled=True,
                  tile_size=(34, 34), tile_stride=(18, 16))
```

Tiny and tiny-long retain methods with these signatures, but their inference
calls decode through an injected `TCDecoder`, not `decode_video`.

## Common Call Signature

The three `__call__` methods have the same parameter list (the full route's
`tea_cache_model_id` default is `"Wan2.1-T2V-1.3B"`; tiny routes use
`"Wan2.1-T2V-14B"`):

```python
pipe(
    prompt=None,
    negative_prompt="",
    denoising_strength=1.0,
    seed=None,
    rand_device="gpu",
    height=480,
    width=832,
    num_frames=81,
    cfg_scale=5.0,
    num_inference_steps=50,
    sigma_shift=5.0,
    tiled=True,
    tile_size=(60, 104),
    tile_stride=(30, 52),
    tea_cache_l1_thresh=None,
    tea_cache_model_id="...",
    progress_bar_cmd=tqdm,
    progress_bar_st=None,
    LQ_video=None,
    is_full_block=False,
    if_buffer=False,
    topk_ratio=2.0,
    kv_ratio=3.0,
    local_range=9,
    color_fix=True,
)
```

Do not copy the generic-looking defaults blindly. The official FlashVSR stream
recipe overrides `cfg_scale=1.0`, `num_inference_steps=1`, and
`if_buffer=True`.

## Operative Call Parameters

| Parameter | Verified effect and decision |
|---|---|
| `LQ_video` | Practical required conditioning tensor, `[1,3,F,H,W]`, bfloat16, `[-1,1]`. Full/tiny keep it on CUDA; tiny-long accepts it on CPU and transfers slices. |
| `height`, `width` | Noise/output geometry. Must equal `LQ_video.shape[-2:]`. Prepare both as 128 multiples; do not rely on the tiny pipeline's 16-pixel round-up because that does not resize `LQ_video`. |
| `num_frames` | Use `F=8n+1`; expected output is `F-4=8n-3`. The implementation only rounds a non-`1 mod 4` value, which is insufficient for the stream indexing. |
| `cfg_scale` | Asserted to be exactly `1.0`; any other value fails immediately. |
| `num_inference_steps` | Pass `1`. `init_cross_kv` fixes timestep 1000 and configures a one-step scheduler. |
| `seed` | Seeds the generated latent noise. Use a fixed integer for repeatability. |
| `if_buffer` | Official calls use `True`, producing latent time `(F-1)//4`; `False` adds one latent time position and is not the verified streaming recipe. |
| `topk_ratio` | Controls LCSA draft-mask selection. Derive it from `sparse_ratio`: `sparse_ratio*768*1280/(H*W)`. Use sparse ratio 1.5 for speed or 2.0 for stability. |
| `kv_ratio` | In the stream wrapper this is converted with `int(kv_ratio)` and used as the retained self-attention cache-group limit. Keep `3.0`; fractional parts have no effect. |
| `local_range` | Rebuilds the locality mask when geometry or range changes. Use 9 for sharper detail or 11 for more stable output. |
| `color_fix` | If true, applies per-chunk/full-output AdaIN color correction against aligned LQ frames. The implementation catches all correction exceptions, so a mismatch may silently skip correction. |
| `tiled` | On full, controls Wan VAE decode tiling: false is faster/higher VRAM; true lowers decode memory with extra work. Tiny/tiny-long inference uses `TCDecoder`, so these VAE tiling arguments do not control its decode path. |
| `tile_size`, `tile_stride` | Full decoder tile geometry; defaults `(60,104)` and `(30,52)` provide overlap. Only relevant when full uses `tiled=True`. |
| `is_full_block` | Threaded through the call but not consulted by the verified streaming self-attention implementation. Keep false. It cannot replace `block_sparse_attn`. |

`prompt`, `negative_prompt`, `denoising_strength`, `rand_device`, `sigma_shift`,
TeaCache arguments, and progress-bar injection are retained in the signature but
do not control the current one-step stream body. Do not use them as tuning
knobs without re-verifying a newer implementation.

## Shapes and Stream Indexing

Given prepared target geometry `H x W` and `F=8n+1`:

1. Input: `LQ_video.shape == [1, 3, F, H, W]`.
2. Buffered noise: `[1, 16, (F-1)//4, H//8, W//8]`.
3. Number of stream iterations: `(F-1)//8 - 2 = n-2`.
4. The first DiT iteration consumes six latent-time positions; later iterations
   consume two. Self-attention starts with `f=6`, then requires `f=2` while
   carrying per-block K/V caches.
5. Expected return from all routes: `[3, F-4, H, W]` in approximately
   `[-1,1]` (the batch dimension is removed).
6. MP4 conversion: permute to `[F-4,H,W,3]`, compute
   `clip((x.float()+1)*127.5, 0, 255)`, and cast to `uint8`.

The first valid recipe with at least one stream iteration is `n=3`, `F=25`,
and 21 output frames.

## LCSA and Cache Mechanics

The stream wrapper patchifies latent input, uses a `(2,8,8)` 3D attention
window, builds a locality mask, scores candidate blocks, and invokes
`block_sparse_attn_func` with that mask. For the stream wrapper:

```text
window_size = 2 * patch_grid_h * patch_grid_w // 128
square_num = window_size * window_size
topk = int(square_num * topk_ratio) - 1
kv_len = int(kv_ratio)
```

The mask is cached per attention block and rebuilt when patch-grid height,
patch-grid width, or `local_range` changes. This behavior supports sequential
calls with different aspect ratios in the current implementation. Each new
pipeline call also clears the LQ projection cache and initializes new streaming
self-attention K/V lists on its first iteration. Cross-attention K/V is retained
from `init_cross_kv`.

`block_sparse_attn` is imported unconditionally at module import and used when
the LCSA mask is present. Dense FlashAttention/SageAttention/SDPA branches do
not serve as a fallback for this masked official path.

## Initialization Contracts

### Model manager

```python
ModelManager(
    torch_dtype=torch.float16,
    device="cuda",
    model_id_list=[],
    downloading_priority=["ModelScope", "HuggingFace"],
    file_path_list=[],
)
mm.load_models(file_path_list, model_names=None,
               device=None, torch_dtype=None)
mm.fetch_model(model_name, file_path=None, require_model_path=False)
```

Use `ModelManager(torch_dtype=torch.bfloat16, device="cpu")` and load explicit
local checkpoint paths. Supplying local paths avoids any downloader route.
Verify that a DiT was detected before constructing the pipeline.

### LQ projection

Every route requires an injected projection:

```python
ProjectionClass(in_dim=3, out_dim=1536, layer_num=1)
pipe.denoising_model().LQ_proj_in = projection
projection.load_state_dict(lq_state, strict=True)
projection.clear_cache()
projection.stream_forward(video_slice)
```

Use `Buffer_LQ4x_Proj` only with v1 and `Causal_LQ4x_Proj` only with v1.1.
These support objects are not exported by the DiffSynth package in the verified
layout; a self-contained deployment must package their official implementation
in an application-owned runtime module rather than import a checkout-relative
example utility.

### Tiny conditional decoder

Tiny and tiny-long require:

```python
build_tcdecoder(
    new_channels=[512, 256, 128, 128],
    new_latent_channels=16 + 768,
)
pipe.TCDecoder.load_state_dict(tcdecoder_state, strict=False)
pipe.TCDecoder.clean_mem()
```

The decoder consumes latent plus pixel-shuffled condition channels, returns RGB,
and keeps temporal memory. Tiny clears memory once per call and decodes the full
latent sequence; tiny-long decodes each stream iteration and retains decoder
memory between chunks.

### Cross-attention context

`init_cross_kv()` without an argument reads a hard-coded relative prompt path.
Avoid that checkout-layout dependency. Load the application-owned context with
`torch.load(..., map_location="cpu", weights_only=True)`, verify tensor shape
`[1,512,4096]`, and pass `context_tensor=context`. The method moves it to the
pipeline device/dtype and initializes every DiT block's cross-attention K/V.

## VRAM Management

`enable_vram_management` wraps selected DiT linear, 3D convolution,
normalization, and RMSNorm modules with CPU-offload-aware layers. Full also
wraps selected VAE modules. `num_persistent_param_in_dit=None` applies the
normal GPU onload configuration to all matched DiT parameters. The pipeline
then enables CPU offload; `load_models_to_device` onloads or offloads wrapped
modules and clears the CUDA allocator cache.

For full inference, dropping the unused VAE encoder before inference is valid
because only decode is called. Do not do this if the same VAE instance must
later encode input.
