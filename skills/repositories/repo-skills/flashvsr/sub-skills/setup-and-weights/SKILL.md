---
name: setup-and-weights
description: "Installs and diagnoses the official FlashVSR CUDA/LCSA runtime,
  validates v1 or v1.1 model bundles, and wires ModelManager, projection,
  decoder, and context assets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# FlashVSR Setup and Weights

Use this sub-skill before any FlashVSR model allocation. It owns the Python,
PyTorch, CUDA, Block-Sparse-Attention, model-bundle, ModelManager, projection,
decoder, and positive-context gates. Route prepared video geometry, temporal
framing, full/tiny/tiny-long selection, and pipeline calls to
[inference](../inference/SKILL.md).

## Route by symptom

- **Fresh install, `pkg_resources`, compiler, CUDA, or extension build:** read
  [install.md](references/install.md).
- **Acquire or validate v1/v1.1 files; wire ModelManager and support modules:**
  read [weights-and-model-manager.md](references/weights-and-model-manager.md).
- **Import, LFS pointer, detector, state-dict, context, or memory failure:** read
  [troubleshooting.md](references/troubleshooting.md).

## Required target profile

The verified backend-smoke profile is Python 3.11, PyTorch 2.6.0+cu124,
CUDA 12.4, and NVIDIA A100 SM80. FlashVSR's official Wan DiT imports and calls
`block_sparse_attn`; a CUDA-enabled torch import alone is not sufficient.
Build the extension separately for the target toolkit/ABI/SM profile and require:

```bash
python -c "from block_sparse_attn import block_sparse_attn_func; print('LCSA import OK')"
```

The import gate and a small bf16 CUDA streaming-attention call passed on the
profile above. Real FlashVSR checkpoint loading remains a separate native gate.
Run the bundled read-only diagnostic from any directory:

```bash
python <skill-root>/sub-skills/setup-and-weights/scripts/check_environment.py
```

It reports target-version and backend readiness without downloading, building,
or printing module/cache locations.

## Version-atomic weight gate

Use one application-owned model directory containing the official v1 **or**
v1.1 files:

```text
diffusion_pytorch_model_streaming_dmd.safetensors
Wan2.1_VAE.pth
LQ_proj_in.ckpt
TCDecoder.ckpt
README.md
```

Before ModelManager, reject missing, empty, and Git LFS pointer files:

```bash
python <skill-root>/sub-skills/setup-and-weights/scripts/check_weights.py \
  <MODEL_DIR> --version v1.1
```

Do not mix versions. Full uses the DiT and Wan VAE; tiny and tiny-long use the
DiT and TCDecoder. All routes use the matching LQ projection and positive
cross-attention context.

## Wiring invariants

- Construct `ModelManager(torch_dtype=torch.bfloat16, device="cpu")`; load
  explicit local files and stop unless `wan_video_dit` is detected. Full must
  also detect `wan_video_vae`.
- v1 uses `Buffer_LQ4x_Proj`; v1.1 uses `Causal_LQ4x_Proj`. Both use
  `(in_dim=3, out_dim=1536, layer_num=1)` and load `LQ_proj_in.ckpt` strictly.
- Tiny routes build TCDecoder with channels `[512,256,128,128]` and latent
  channels `16+768`; load non-strictly but review all missing/unexpected keys.
- Package projection/decoder support in the application. They are not stable
  public `diffsynth` exports; do not depend on a source-checkout utility path.
- Load an application-owned context tensor, require shape `[1,512,4096]`, and
  call `pipe.init_cross_kv(context_tensor=context)` once before inference.

## Verification boundary

Completed: package and FlashVSR-class imports, CUDA hardware probe,
`block_sparse_attn` import, bf16 kernel smoke, diagnostic helper checks, and
synthetic incomplete-bundle checks. Not completed: real v1/v1.1 checkpoint
loading, strict projection/decoder compatibility against published weights, or
full/tiny/tiny-long model inference. Do not promote setup checks into an
end-to-end inference claim.
