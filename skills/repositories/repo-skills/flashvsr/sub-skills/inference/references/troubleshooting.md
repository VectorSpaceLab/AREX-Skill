# FlashVSR Inference Troubleshooting

Use this by symptom. Perform input/backend checks before loading checkpoints,
and change one parameter at a time. No recovery below downloads models or
requires access to an original checkout.

## Install, Import, and Backend

### `ModuleNotFoundError: No module named 'block_sparse_attn'`

**Cause:** the Wan DiT module imports the block-sparse extension
unconditionally. The official LCSA path requires `block_sparse_attn_func`.

**Recover:**

1. Confirm the target environment uses the intended Python, PyTorch, CUDA
   runtime, compiler, and GPU architecture.
2. Build/install Block-Sparse-Attention against that exact PyTorch/CUDA
   combination. Parallel Ninja compilation can consume substantial host RAM;
   reduce build parallelism (for example, `MAX_JOBS=1`) if compilation is
   killed or OOMs.
3. Start a new Python process and require this gate to pass:

   ```bash
   python -c "from block_sparse_attn import block_sparse_attn_func; print('LCSA import OK')"
   ```

4. Only then test `from diffsynth import FlashVSRTinyPipeline`.

The prepared profile is Python 3.11, PyTorch 2.6.0+cu124, CUDA 12.4, and A100
SM80. A100/A800 are documented as intended acceleration targets and H200 as
functional with limited acceleration; other GPU behavior is not established by
this skill. The extension import and a small bf16 CUDA kernel smoke passed on the prepared
A100 SM80 target; real FlashVSR checkpoint inference remains unverified.

**Do not:** set `is_full_block=True` and expect a dense fallback. Current stream
self-attention does not branch on this flag and still builds/calls LCSA.

### Undefined symbols, CUDA invalid device function, or extension crash

**Cause:** an extension compiled for a different PyTorch ABI, CUDA toolkit, or
SM architecture; or an unsupported GPU.

**Recover:** remove the stale extension build artifacts, rebuild in the target
environment for its GPU architecture, and rerun the isolated import gate. Then
run a tiny kernel/package smoke check supplied by the extension project before
FlashVSR. Stop and report a backend block if the extension cannot pass its own
check; do not claim official inference verification.

### `diffsynth` imports, but a FlashVSR class is absent

**Cause:** a different DiffSynth distribution/version is first on `sys.path`.

**Recover:** inspect the imported distribution version and exported names,
remove path shadowing, and install a package build containing all three
`FlashVSR*Pipeline` exports. Do not fix this by adding an original checkout to
`sys.path`; use a self-contained installed runtime.

### Model manager says it cannot detect a model, or `pipe.dit`/`pipe.vae` is `None`

**Cause:** wrong filename/content, incomplete large-file checkout, a version
mix, or omission of the full route's VAE file.

**Recover:** verify files are non-placeholder binary checkpoints, use exact
route requirements from [workflows.md](workflows.md), load the DiT first and VAE
for full, then assert fetched models are non-`None`. Never continue to
`enable_vram_management` with a missing required model.

## Model Wiring and Initialization

### `AttributeError` involving `LQ_proj_in`, `TCDecoder`, or `stream_forward`

**Cause:** support components were not injected, a generic class was used, or a
checkout-relative utility import disappeared in deployment.

**Recover:** package the official support components in an application-owned
runtime module. Inject `Buffer_LQ4x_Proj` for v1 or `Causal_LQ4x_Proj` for v1.1
with `(in_dim=3,out_dim=1536,layer_num=1)`. For tiny routes also inject the tiny
conditional decoder with channels `[512,256,128,128]` and latent channels
`16+768`. Do not point runtime code to an examples directory.

### Strict LQ projection state-dict mismatch

**Cause:** v1/v1.1 projection class and checkpoint were mixed, or the file is
wrong/corrupt.

**Recover:** keep the version directory atomic. Load `LQ_proj_in.ckpt` into the
matching projection with `strict=True`; do not suppress missing/unexpected keys.
Re-select the version rather than editing keys by hand.

### Tiny decoder reports many missing/unexpected keys

**Cause:** wrong `TCDecoder.ckpt`, wrong decoder channel construction, or a
version mix. Its official load uses `strict=False`, so execution can otherwise
continue with an invalid partial load.

**Recover:** construct exactly `new_channels=[512,256,128,128]` and
`new_latent_channels=784`, use the matching version's checkpoint, print and
review the load result, and stop on unexplained key mismatches.

### Cross-attention KV not initialized, prompt file missing, or hard-coded path error

**Symptoms:** a runtime message asking for `pipe.init_cross_kv()`, a
`FileNotFoundError` for a relative positive-prompt path, or an assertion inside
cross-attention.

**Cause:** `init_cross_kv` was omitted or its no-argument hard-coded path does
not exist outside the source layout.

**Recover:** load the positive context tensor from an application-owned asset,
check that it is a tensor of shape `[1,512,4096]`, then call:

```python
context = torch.load(path, map_location="cpu", weights_only=True)
pipe.init_cross_kv(context_tensor=context)
```

Call it after injecting/loading the DiT and before inference. Reuse the cache
across clips only when the context is unchanged.

## Geometry and Frames

### Validator rejects non-128 prepared geometry

**Symptom:** `prepared geometry must be divisible by 128`.

**Cause:** already-prepared `LQ_video` dimensions violate the official spatial
contract.

**Recover:** return to source frames, bicubic-upscale by 4, floor each scaled
dimension to a positive 128 multiple, and center-crop. Re-run:

```bash
python <skill-root>/sub-skills/inference/scripts/validate_input.py \
  --geometry-mode prepared --width TARGET_W --height TARGET_H --frames REAL_FRAMES
```

Do not round only `height`/`width` arguments; the tensor must have the same
aligned geometry.

### Tensor-size mismatch, attention window assertion, or concatenate error

**Likely causes:**

- `LQ_video.shape[-2:]` differs from `(height,width)`.
- input frame images have inconsistent sizes.
- a scalar dimension was rounded without resizing the tensor.
- width/height are only 16-aligned rather than prepared as 128 multiples.

**Recover:** run the bundled validator against the directory/video, verify all
frames are RGB-convertible and identical in size, rebuild the tensor once, and
assert:

```python
assert LQ.ndim == 5 and LQ.shape[:2] == (1, 3)
assert LQ.shape[-2:] == (H, W)
assert H % 128 == 0 and W % 128 == 0
```

### Empty output, `torch.cat` on an empty list, or too few stream iterations

**Cause:** `num_frames` may satisfy `1 mod 4` but not the stronger `8n+1`
stream rule, or it is below the first usable `F=25`.

**Recover:** require at least 21 real frames, prepare `F=8n+1`, and expect
`F-4=8n-3`. Use the validator; do not rely on the pipeline's internal frame
rounding.

### Output has fewer frames than the source

**Cause:** the official floor policy chooses the largest output count `8n-3`
not exceeding the source and uses four future/repeated conditioning frames.
This can drop up to seven source-tail frames.

**Recover:** if exact duration matters, validate with
`--frame-policy preserve-all`, repeat-pad to the next valid `F`, run inference,
and trim repeated output back to the real source count. Preserve the source FPS.

### Aspect-ratio change produces stale-mask artifacts

**Cause:** an older implementation may retain a locality mask across different
geometries. The verified implementation rebuilds when patch-grid height,
patch-grid width, or `local_range` changes.

**Recover:** confirm the installed implementation has all three cache-key
checks. If uncertain, instantiate a fresh pipeline for the new geometry. Do not
reuse partially initialized stream K/V from an interrupted call.

## CUDA and Memory

### CUDA out of memory during input preparation or DiT

**Cause:** full prepared video was placed on CUDA, target area is too large, or
another clip/model still owns memory.

**Recover in order:**

1. Finish/release the current clip; remove stale tensors and clear allocator
   cache before the next attempt.
2. Switch from full/tiny to tiny-long so the prepared LQ tensor stays on CPU and
   only slices transfer to CUDA.
3. Reduce target resolution while keeping both dimensions 128-aligned.
4. Change `sparse_ratio` from 2.0 to 1.5 after comparing quality. This can
   reduce sparse attention work but is not guaranteed to solve every peak.
5. Process valid temporal segments independently instead of one giant tensor.

Keep `enable_vram_management(num_persistent_param_in_dit=None)` and CPU offload
wiring. Do not disable LCSA or change `if_buffer=True` as an ad hoc recovery.

### CUDA OOM during full VAE decode

**Cause:** full used `tiled=False` at large spatial geometry.

**Recover:** retry full with `tiled=True`, default overlapping tile size
`(60,104)`, and stride `(30,52)`. Tiling is slower but lowers decode memory. If
it still fails, reduce geometry or switch to tiny/tiny-long. Tiny route call
arguments named `tiled`, `tile_size`, and `tile_stride` do not govern its
`TCDecoder` inference path.

### Tiny-long avoids CUDA OOM but host is killed or swapping

**Cause:** tiny-long is GPU-streaming, not constant-host-memory: it retains the
complete prepared LQ tensor on CPU and accumulates decoded CPU chunks before
concatenation. A 4x high-resolution long clip can require tens of GiB.

**Recover:** estimate `1*3*F*H*W*2` bytes for just the bfloat16 input, plus output
and overhead. Segment before tensor construction, keep segments valid under the
frame rule, trim overlap/repeated tails deterministically, and encode completed
segments incrementally.

### Tiled decode seams or edge artifacts

**Cause:** inadequate overlap, custom tile geometry, or a quality difference
between tiled and untiled decode.

**Recover:** restore default tile/stride overlap, compare a short aligned clip
with `tiled=False` if memory permits, and only then adjust one tile dimension at
a time. Keep target geometry 128-aligned.

## Quality and Color

### Fine detail degrades or texture aliases

**Cause:** LCSA is absent/bypassed in a nonofficial implementation, sparse ratio
is too aggressive, or local range is unsuitable.

**Recover:** first prove the block-sparse extension import and use the official
pipeline. Restore `sparse_ratio=2.0`, `local_range=11`, `kv_ratio=3.0`, and
`is_full_block=False`. Compare `local_range=9` only when sharper detail is worth
the stability trade-off.

### Color correction appears ineffective or colors shift

**Cause:** `color_fix=True` uses AdaIN against aligned LQ frames, but correction
is wrapped in a broad exception handler and may be silently skipped on a shape
or device mismatch.

**Recover:** assert returned and conditioning tensors share channel/time/spatial
shape for the corrected range. Compare a fixed clip with `color_fix=True` and
`False`. If correction is unexpectedly identical, instrument the application
around the correction call or temporarily invoke the corrector explicitly so
exceptions are visible; do not assume it succeeded.

### Nondeterministic result despite fixed input

**Cause:** missing seed, different extension/kernel build, changed geometry,
weights, dtype, or sparse settings.

**Recover:** pin version/route/model files, `seed`, bfloat16, geometry, frame
plan, sparse/local/cache parameters, PyTorch/CUDA/extension build, and output
codec. A fixed seed alone does not guarantee bitwise equality across kernels.

## MP4 Output

### `imageio` cannot find FFmpeg or `libx264`

**Symptoms:** `No such file or directory: ffmpeg`, codec-not-found, encoder
initialization failure, or an empty MP4.

**Cause:** `imageio-ffmpeg`/FFmpeg is absent or the build lacks H.264 encoding.

**Recover:**

1. Install/verify `imageio` and `imageio-ffmpeg` in the runtime environment.
2. Confirm the FFmpeg binary can list encoders and that `libx264` is available.
3. If H.264 is unavailable, choose a codec actually provided by that FFmpeg
   build and record the compatibility change.
4. Write to a local, writable parent directory and close the writer.

Do not redownload or rerun inference until validating the already-produced RGB
frames.

### Writer rejects frame shape/dtype or output colors are wrong

**Cause:** model tensor was not permuted/denormalized, a batch dimension remains,
or frames are not contiguous RGB uint8.

**Recover:** verify model output `[3,T,H,W]`, permute to `[T,H,W,3]`, compute
`((x.float()+1)*127.5).clamp(0,255)`, cast to `uint8`, move to CPU, and append
one `H x W x 3` array at a time.

### MP4 duration/FPS mismatch

**Cause:** fallback FPS was used, output alignment removed tail frames, or
repeat-padded output was not trimmed.

**Recover:** inspect source FPS, validator `expected_output_frames`, and selected
frame policy. With preserve-all, trim output to the real frame count before
writing. Re-open the MP4 and verify frame count, geometry, and FPS as metadata,
not only file existence.
