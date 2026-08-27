# External models, caches, and safe alternatives

The three embedding wrappers are adapters around pretrained models, not small
local layers. Their constructors can resolve source code, tokenizer files,
configuration, and weights. Treat acquisition as an explicit deployment step;
do not construct a wrapper merely to learn whether it downloads.

## External-model matrix

| Wrapper | Constructor action | External width | Requested representation |
|---|---|---:|---|
| `ESMEmbedWrapper` | `torch.hub.load("facebookresearch/esm", "esm1b_t33_650M_UR50S")` | 1280 | Layer 33 |
| `MSAEmbedWrapper` | `torch.hub.load("facebookresearch/esm", "esm_msa1_t12_100M_UR50S")` | 768 | Layer 12 |
| `ProtTranEmbedWrapper` | Hugging Face `from_pretrained("Rostlab/prot_bert")` for tokenizer and model | 1024 | Transformers feature-extraction output |

The ESM constructors load through `torch.hub` in `__init__`. The ProtTrans
constructor imports `transformers` and invokes both Hugging Face loaders in
`__init__`. None exposes a deferred-load or explicit local-only option.

`transformers` is declared by the package metadata. The ESM hub repository,
pretrained assets, and NVIDIA Apex are not ordinary pinned package
dependencies. A successful `import alphafold2_pytorch` proves none of those
assets or native operations.

## Approval gate before construction

Confirm all of these before calling a wrapper constructor:

1. **Acquisition policy:** exact source and weights are already staged, or
   network access, license review, download size, and cache writes are
   explicitly approved.
2. **Cache:** the executing user can read it, it contains source plus the exact
   model/tokenizer/configuration assets, and enough disk remains for load-time
   extraction or updates.
3. **Runtime:** the selected torch, `transformers`, hub code, and serialized
   weights are mutually compatible.
4. **Native operations:** any Apex/fused operation required by the selected
   external model is already validated for the torch/CUDA/compiler stack.
5. **Resources:** the model plus `(B, M, N)` workload fits the selected device.
6. **Source limitations:** the wrapper defects in
   [API reference](api-reference.md) have an approved compatibility plan.

A non-mutating torch-hub cache-location probe is:

```bash
python - <<'PY'
import torch
print(torch.hub.get_dir())
PY
```

Printing a cache location does not prove that it is complete or compatible.
For Hugging Face, use the cache/offline controls supported by the approved
`transformers` and `huggingface_hub` versions. The wrapper itself does not pass
`local_files_only=True`; do not assume it enforces offline behavior. If the
runtime supports `HF_HUB_OFFLINE` or `TRANSFORMERS_OFFLINE`, setting it before
process startup can make an intended cache-only check fail closed, but missing
assets must then remain a visible error rather than triggering a download.

## `torch.hub` versus Hugging Face

Keep these failure domains separate:

- `torch.hub` needs a compatible repository snapshot and the requested ESM
  entry point; the entry point may then resolve pretrained weights.
- Hugging Face needs model configuration, tokenizer vocabulary/configuration,
  and weight files for `Rostlab/prot_bert`, plus compatible `transformers`
  behavior.
- Cache success on one machine, user, package version, or device does not prove
  another environment can deserialize or execute the same files.
- Repeated constructor retries can repeat network, extraction, allocation, and
  cache mutation. Do not use retries as discovery.

## Apex and fused-operation boundary

The README says the pretrained transformers require NVIDIA Apex because they
use fused operations and provides a CUDA/C++ build recipe. The package metadata
does not pin Apex. That README statement is a prerequisite warning, not proof
that every wrapper needs the same kernel or that any arbitrary Apex build is
compatible.

Apex installation can compile native code and depends on the exact torch,
CUDA, compiler, GPU, and ABI combination. Never launch such a build as a
surprise recovery step. If a cached model fails in Apex or a fused operator:

- preserve the full missing-symbol or compiled-extension error;
- record torch/CUDA/Apex/compiler versions and the requested model;
- use an already validated environment, or ask before creating a separate
  native build; and
- prefer precomputed representations when the goal is to exercise only the
  Alphafold2 trunk.

CPU package import and CPU core inference do not validate Apex. CUDA visibility
also does not prove an allocation or fused kernel will succeed.

## Safe precomputed-representation route

When assets or external execution are not approved, use local features only:

1. Establish the feature meaning and residue/MSA row ordering.
2. Validate `precomputed.shape == (B, M, N, E)` and set
   `Alphafold2(num_embedds=E)`; the release default is `E=1280`.
3. Project with `projected = model.embedd_project(precomputed)` to obtain
   `(B, M, N, model.dim)`.
4. Supply explicit `msa_embed=projected` and a separately validated
   `seq_embed: (B, N, model.dim)`. If row 0 intentionally represents the
   primary sequence, `projected[:, 0]` can supply it.
5. Supply aligned integer tokens and boolean masks. With
   `disable_token_embed=True`, both explicit representations are mandatory.

[`embedding_input_smoke.py`](../scripts/embedding_input_smoke.py) follows this
bounded route with synthetic `(B, M, N, 1280)` features, CPU by default, no
files, no model hosts, and output-shape assertions. It also reports the direct
`embedds` limitation described below.

The source contains a direct `embedds` argument, but 0.4.32 initializes an MSA
before its `elif embedds` branch and thereby shadows that branch. Passing an
explicit MSA also selects the earlier token-MSA path. Consequently, a normal
unmodified forward call must not be claimed to consume `embedds`; use the
explicit projected representations above or validate a reviewed core adapter.

## Limits of this route

- It validates shape flow and the Alphafold2 projection/trunk, not biological
  quality or equivalence to a named pretrained model.
- A 768-wide MSA Transformer tensor or 1024-wide ProtBERT tensor needs matching
  `num_embedds`; do not pass it to the default 1280-input projection.
- The wrappers' own `project_embed` layers are distinct from the core
  `embedd_project` and have different learned parameters.
- Pretrained downloads, cache staging, training/data pipelines, CUDA execution,
  Apex builds, and fused kernels are outside the safe synthetic check.
- The ESM and MSA wrappers have source defects detailed in
  [API reference](api-reference.md); successful asset acquisition would not by
  itself make those paths operational.
