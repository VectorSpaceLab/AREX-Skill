# Embedding troubleshooting

Isolate the failing stage: package import, external-model acquisition, feature
conversion, projection, or core trunk. Keep the no-network synthetic check
available so a model-host failure is not mistaken for a trunk failure.

## Missing `transformers` or ProtTrans model assets

**Symptoms:** `ModuleNotFoundError: transformers`; configuration/tokenizer/model
errors while constructing `ProtTranEmbedWrapper`; or a failure in the
feature-extraction pipeline.

**Actions:**

1. Remember that `transformers` is imported by the ProtTrans constructor, not
   by a minimal package import check.
2. Confirm the exact `Rostlab/prot_bert` tokenizer, configuration, and weights
   are already staged in an approved cache, or obtain explicit approval for
   network/cache acquisition. The wrapper has no `local_files_only` parameter.
3. Confirm the sequence is a rank-2 integer tensor and that conversion through
   the package vocabulary produces space-separated amino-acid text. The helper
   normalizes `U`, `Z`, `O`, and `B` to `X`.
4. If external assets are not approved, stop using the wrapper and run
   `embedding_input_smoke.py`; do not silently substitute another checkpoint.

## `torch.hub`, network, and cache failures

**Symptoms:** HTTP/DNS/repository/archive/permission/checkpoint errors, a hub
constructor hanging, or one user/device finding a cache that another cannot.

**Actions:**

- Verify the exact requested entries: `esm1b_t33_650M_UR50S` for ESM and
  `esm_msa1_t12_100M_UR50S` for MSA Transformer.
- Treat hub source code and model weights as separate cache requirements.
  Check permissions, free disk, and compatibility without deleting or
  overwriting approved assets.
- Do not retry a network constructor by default. If staging is not approved,
  use the no-network synthetic/precomputed path.
- A successful asset load still does not validate the 0.4.32 helper shape or
  MSA helper defects.

## Apex and fused operations

**Symptoms:** missing Apex, fused layer normalization/attention symbols,
missing CUDA extensions, ABI/compiler errors, or a wrapper that constructs but
fails on first forward.

The README calls Apex/fused operations a pretrained-transformer prerequisite,
but `setup.py` does not pin Apex. Preserve the complete traceback and record
torch, CUDA, compiler, GPU, Apex, and model versions. Do not compile or install
Apex as an unapproved surprise fix. Use an already validated native runtime,
or ask for a separately scoped build. A CPU core pass and
`torch.cuda.is_available()` are not proof of Apex or fused-kernel support.

## Sequence/MSA width mismatch

**Symptoms:**

- `MSAEmbedWrapper` raises `sequence and msa must have the same length if you
  wish to use MSA transformer embeddings`.
- The core raises `sequence length of MSA and primary sequence must be the same`.
- `einops` fails while flattening/restoring rows.

For this release, use `seq: (B,N)`, `msa: (B,M,N)`, and `msa_mask: (B,M,N)`
with the same final `N`. The README contains an older example/comment saying
MSA width can differ; source asserts equality in both the wrapper and core.
Do not crop biological sequences casually. Resolve the alignment, rebuild or
pad all rows consistently, and regenerate masks on the same residue axis.

## MSA mask and padded-row behavior

`MSAEmbedWrapper` treats `msa_mask` as a way to avoid passing fully padded rows
to the model, but its source counts valid original MSA rows after the sequence
has been prepended. This can retain one too few rows when all rows are valid,
and can remove the prepended sequence row when no MSA row is valid. If output
rows or downstream shapes look wrong, inspect valid-row counts and compare with
an unmasked call. Treat a reviewed helper fix or precomputed route as the safe
recovery; a mask does not correct a row-count bug.

## Disabled token embeddings

**Symptoms:** `sequence embedding must be supplied if one has disabled token
embedding`, `msa embedding must be supplied if one has disabled token embedding`,
or an ESM call with `msa=None` failing at the start of the core.

The core adds supplied representations to token embeddings by default. With
`disable_token_embed=True`, it requires both `seq_embed: (B,N,D)` and
`msa_embed: (B,M,N,D)` immediately. The lower-level `embedds` tensor does not
satisfy these checks. Use token embeddings while isolating the pipeline, or
pass both explicit projected representations from a validated wrapper/adapter.
ESM's optional `msa=None` form supplies only a sequence representation and is
therefore incompatible with this flag.

## Direct `embedds` appears ignored

The checked source turns `msa=None` into `seq[:, None, :]` before selecting the
MSA branch, and an explicit MSA also selects that branch. Its later
`elif exists(embedds)` branch is therefore shadowed in ordinary calls. If
changing `(B,M,N,1280)` features does not change a call that supplies MSA, that
is source control flow, not a mask issue. Use `model.embedd_project` plus
explicit `seq_embed`/`msa_embed`, or route a production fix through a reviewed
core-model adapter. The bundled smoke intentionally checks projection and a
normal core pass separately rather than claiming direct consumption.

## MSA helper failure

**Symptom:** `NameError: name 'seq' is not defined` from `get_msa_embedd`.

The helper parameter is named `msa`, but the implementation assigns
`device = seq.device`. Confirm this traceback before changing data or installing
packages. A reviewed local correction to `msa.device` still needs validation of
model output, layer extraction, row restoration, masks, and device placement.
Until then, use precomputed representations.

## ESM helper/wrapper shape failure

**Symptoms:** constructor succeeds but forward rejects an unexpected keyword,
sequence embedding addition gets an extra singleton axis, or `einops` rejects
the flattened MSA output.

In this source, `ESMEmbedWrapper` passes `device=device` to a helper that does
not declare `device`, yielding an unexpected-keyword `TypeError`. If corrected,
`get_esm_embedd` adds a singleton axis and returns `(B,1,N,1280)` while the
wrapper/core sequence contract is `(B,N,D)`; its MSA reshape also assumes fewer
axes. Preserve the traceback, use precomputed features, or validate a reviewed
compatibility patch. Do not attribute this to an incorrectly returned model
layer without checking the helper call and shape.

## OOM and device pressure

**Symptoms:** model load or feature extraction exhausts CPU/GPU memory, a tiny
core pass succeeds but a wrapper fails, or CUDA is visible but allocation fails.

Reduce `B`, `M`, and `N` before changing code; avoid duplicate model instances;
free unrelated allocations; and move to a device only after that device is
explicitly tested. Chunk MSA rows only if row ordering and wrapper semantics
are preserved. Record model source, tensor shapes, dtype, device, and allocator
error. Do not repeatedly reload/download after an OOM. If the task is only to
exercise the trunk, use precomputed features and the CPU-default smoke. CUDA
availability is not evidence that shared-device allocation or wrapper forward
will succeed.
