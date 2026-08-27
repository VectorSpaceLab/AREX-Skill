# Core workflows

These examples use only deterministic synthetic tensors. They do not download
models, read datasets, or run the repository's native tests/examples. Run in an
environment where `alphafold2_pytorch==0.4.32` imports successfully.

## 1. Basic sequence plus MSA

Use `eval()` and `no_grad()` for an inference smoke. Keep the MSA width equal
to the sequence width even though the README says otherwise.

```python
import torch
from alphafold2_pytorch import Alphafold2

B, M, N = 1, 2, 8
model = Alphafold2(dim=16, depth=1, heads=1, dim_head=16)
model.eval()
seq = torch.arange(N).view(1, N) % 21
msa = torch.arange(B * M * N).view(B, M, N) % 21
mask = torch.ones(B, N, dtype=torch.bool)
msa_mask = torch.ones(B, M, N, dtype=torch.bool)

with torch.no_grad():
    ret = model(seq, msa, mask=mask, msa_mask=msa_mask)
assert tuple(ret.distance.shape) == (B, N, N, 37)
print(tuple(ret.distance.shape), type(ret).__name__)
```

## 2. Sequence-only / no-MSA fallback

Omit `msa`, but do not omit `mask`: the implementation creates a one-row MSA
and immediately derives its mask by rearranging `mask`.

```python
model = Alphafold2(dim=16, depth=1, heads=1, dim_head=16).eval()
seq = torch.randint(0, 21, (1, 8))
mask = torch.ones(1, 8, dtype=torch.bool)
with torch.no_grad():
    ret = model(seq, mask=mask)
assert tuple(ret.distance.shape) == (1, 8, 8, 37)
```

A separate `msa_mask` is not a substitute in this route; the fallback derives
`(B, 1, N)` from `mask` and overwrites it.

## 3. Distogram plus angle logits

Set `predict_angles=True` at construction. Read attributes on the
`ReturnValues` object; do not tuple-unpack the result.

```python
model = Alphafold2(
    dim=16, depth=1, heads=1, dim_head=16, predict_angles=True
).eval()
seq = torch.randint(0, 21, (1, 8))
msa = torch.randint(0, 21, (1, 2, 8))
mask = torch.ones(1, 8, dtype=torch.bool)
msa_mask = torch.ones(1, 2, 8, dtype=torch.bool)
with torch.no_grad():
    ret = model(seq, msa, mask=mask, msa_mask=msa_mask)
assert tuple(ret.distance.shape) == (1, 8, 8, 37)
assert tuple(ret.theta_logits.shape) == (1, 8, 8, 25)
assert tuple(ret.phi_logits.shape) == (1, 8, 8, 13)
assert tuple(ret.omega_logits.shape) == (1, 8, 8, 25)
```

## 4. Template feature and angle routes

The current API consumes already-prepared template features, not the README's
`templates_seq`/`templates_coors`/`templates_sidechains` names. With default
constructor widths use `(B, T, N, N, 32)` pair features and `(B, T, N, 55)`
angle features. `templates_mask` is required for either route.

```python
B, T, N, M = 1, 2, 8, 2
model = Alphafold2(
    dim=16, depth=1, heads=1, dim_head=16,
    templates_dim=32, templates_angles_feats_dim=55,
    predict_angles=True,
).eval()
seq = torch.randint(0, 21, (B, N))
msa = torch.randint(0, 21, (B, M, N))
mask = torch.ones(B, N, dtype=torch.bool)
msa_mask = torch.ones(B, M, N, dtype=torch.bool)
templates_feats = torch.randn(B, T, N, N, 32)
templates_angles = torch.randn(B, T, N, 55)
templates_mask = torch.ones(B, T, N, dtype=torch.bool)
with torch.no_grad():
    ret = model(
        seq, msa, mask=mask, msa_mask=msa_mask,
        templates_feats=templates_feats,
        templates_angles=templates_angles,
        templates_mask=templates_mask,
    )
assert tuple(ret.distance.shape) == (B, N, N, 37)
assert tuple(ret.theta_logits.shape) == (B, N, N, 25)
```

Template coordinate meaning and structure/refinement consequences belong to
[structure-and-recycling](../../structure-and-recycling/SKILL.md).

## 5. Extra MSA route

`extra_msa` is an input option for the extra-MSA Evoformer. In the inspected
commit its embedding line accidentally uses `msa` rather than `extra_msa`; use
the same `(B, M, N)` shape as the regular MSA for a conservative smoke and
record this limitation rather than assuming the extra values were consumed.

```python
model = Alphafold2(
    dim=16, depth=1, heads=1, dim_head=16,
    extra_msa_evoformer_layers=1,
).eval()
seq = torch.randint(0, 21, (1, 8))
msa = torch.randint(0, 21, (1, 2, 8))
extra_msa = torch.randint(0, 21, (1, 2, 8))
mask = torch.ones(1, 8, dtype=torch.bool)
msa_mask = torch.ones(1, 2, 8, dtype=torch.bool)
extra_msa_mask = torch.ones(1, 2, 8, dtype=torch.bool)
with torch.no_grad():
    ret = model(
        seq, msa, mask=mask, msa_mask=msa_mask,
        extra_msa=extra_msa, extra_msa_mask=extra_msa_mask,
    )
assert tuple(ret.distance.shape) == (1, 8, 8, 37)
```

## 6. Supplied embedding route and token disabling

For direct supplied embeddings use `seq_embed=(B, N, dim)` and
`msa_embed=(B, M, N, dim)`. Setting `disable_token_embed=True` requires both
arguments by explicit assertions; it does not mean that only one embedding
can be supplied.

```python
B, M, N, D = 1, 2, 8, 16
model = Alphafold2(
    dim=D, depth=1, heads=1, dim_head=D,
    disable_token_embed=True,
).eval()
seq = torch.randint(0, 21, (B, N))
msa = torch.randint(0, 21, (B, M, N))
mask = torch.ones(B, N, dtype=torch.bool)
msa_mask = torch.ones(B, M, N, dtype=torch.bool)
seq_embed = torch.randn(B, N, D)
msa_embed = torch.randn(B, M, N, D)
with torch.no_grad():
    ret = model(
        seq, msa, mask=mask, msa_mask=msa_mask,
        seq_embed=seq_embed, msa_embed=msa_embed,
    )
assert tuple(ret.distance.shape) == (B, N, N, 37)
```

`embedds` appears in the signature with an intended projected last width of
`num_embedds`, but its branch is unreachable in this version because the
missing-MSA fallback creates `msa` before branch selection. Use the dedicated
[embeddings](../../embeddings/SKILL.md) route for external model wrappers and
network/download requirements.

## 7. Run the bundled helper

The helper accepts an optional device, defaults to CPU, and uses tiny synthetic
inputs. Resolve `<core-model>` to this skill directory; no working-directory
change is needed:

```bash
python <core-model>/scripts/core_smoke.py --device cpu
python <core-model>/scripts/core_smoke.py --device cpu --angles --templates --embedding-input
```

A CUDA argument is opt-in only. CUDA was visible during preparation but a
shared-device allocation smoke was blocked by OOM, so use CPU as the verified
baseline.
