# FlashVSR setup troubleshooting

## `ModuleNotFoundError: pkg_resources` during `pip install -e .`

`setup.py` imports `pkg_resources` before setuptools processes the project and
uses its requirement parser. Probe with:

```bash
python -c "import pkg_resources; print('pkg_resources OK')"
```

If absent, install a compatible setuptools release in the active Python 3.11
environment, for example `python -m pip install 'setuptools<81'`, rerun the
probe, and retry the editable install. Do not use a different Python
interpreter by accident.

## Torch/CUDA wheel mismatch

The target torch trio is `2.6.0+cu124`, `0.21.0+cu124`, and `2.6.0+cu124`.
Check both the wheel and toolkit:

```bash
python -c "import torch; print(torch.__version__, torch.version.cuda)"
nvcc -V
```

A CUDA-enabled torch import alone does not prove that the local `nvcc` can
compile the extension. If pip selected a CPU wheel, a different CUDA build, or
an unsupported Python ABI, recreate the isolated environment and install the
pinned cu124 trio from the intended index.

## `No module named block_sparse_attn`

The Wan DiT imports the extension unconditionally, so this is a hard blocker,
not a warning. Recheck that the extension was installed with the same Python
used to run FlashVSR and run:

```bash
python -c "from block_sparse_attn import block_sparse_attn_func; print('LCSA import OK')"
```

Do not switch to `is_full_block=True` as a supposed dense fallback; the
verified streaming route still requires the LCSA function.

## Build is killed, swaps, or runs out of memory

The upstream README warns that parallel compilation is memory intensive. Start
with a single A100 target and one job:

```bash
export BLOCK_SPARSE_ATTN_FORCE_BUILD=TRUE
export BLOCK_SPARSE_ATTN_CUDA_ARCHS=80
export MAX_JOBS=1
export NVCC_THREADS=1
python setup.py install
```

Only widen architecture targets or increase parallelism after the narrow build
and import pass. Remove stale build artifacts only when restarting a deliberate
rebuild; do not confuse a leftover package with a verified import.

## Undefined symbol, invalid device function, or extension crash

These errors usually indicate a mismatch among torch's C++ ABI, the CUDA
runtime/toolkit, compiler, or the compiled SM target. Confirm, in one shell,
Python version, torch version, torch-reported CUDA, `nvcc -V`, compiler version,
and GPU capability. For the target A100, compile SM80 only. Rebuild with the
active environment and a consistent compiler/toolkit. The extension import gate and small bf16 streaming-attention smoke passed on
the prepared A100/SM80 profile. A real FlashVSR checkpoint run is still a
separate native verification item.

## LFS clone contains tiny text files

Run the local checker:

```bash
python <skill-root>/sub-skills/setup-and-weights/scripts/check_weights.py \
  <MODEL_DIR> --version v1.1
```

A file beginning with `version https://git-lfs.github.com/spec/v1` is a pointer,
not a checkpoint. Install Git LFS, rerun `git lfs pull` in the selected version
checkout, and repeat the checker. Do not load a pointer through ModelManager.

## ModelManager cannot detect a model

`ModelManager.load_model()` prints a diagnostic and continues when no detector
matches. Check that:

1. the path points to the non-empty local checkpoint, not a pointer;
2. the file is from the same v1 or v1.1 directory as the projection/decoder;
3. the pinned package and torch environment is active; and
4. the DiT file is passed as an explicit path.

For full, the VAE file must additionally resolve to `wan_video_vae`. Stop if
`fetch_model("wan_video_dit")` or `fetch_model("wan_video_vae")` is `None`.

## `LQ_proj_in` or `stream_forward` errors

Use the exact version-matched projection:

- v1: `Buffer_LQ4x_Proj` plus v1 `LQ_proj_in.ckpt`;
- v1.1: `Causal_LQ4x_Proj` plus v1.1 `LQ_proj_in.ckpt`.

Load the state dict with `strict=True`, retain the module's cache lifecycle,
and initialize it after constructing the pipeline. The projection support classes are not stable public exports; a deployment
must package them rather than depending on a working-directory utility import.

## TCDecoder missing/unexpected keys

The tiny and tiny-long examples construct the decoder with
`new_channels=[512, 256, 128, 128]` and `new_latent_channels=16+768`, then load
the version-matched checkpoint with `strict=False`. Print and review the
returned `missing_keys` and `unexpected_keys`; do not hide them. Full uses the
Wan VAE and does not use TCDecoder.

## `posi_prompt.pth` or cross-KV initialization fails

The context tensor is separate from the five-file model bundle. Confirm that
the application-owned context is loaded on CPU and has shape `[1, 512, 4096]`,
then call `pipe.init_cross_kv(context_tensor=context)` once before inference.
Avoid relying on a checkout-relative path in a portable deployment.

## GPU memory failure after setup

Setup success does not imply inference success. First reduce the selected
inference route: use tiny or tiny-long, keep the prepared input on CPU for
long-video processing, and load only the required route assets. For full,
consider the documented decode-only VAE memory reduction and VAE tiling. Clear
per-clip tensors/cache between clips. Record an actual OOM recovery separately;
it is a deferred native verification candidate, not a setup pass.
