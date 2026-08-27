# Core troubleshooting

## Import and installation

`alphafold2_pytorch.alphafold2` imports `alphafold2_pytorch.utils`, so a core
import exercises more than PyTorch. The package metadata declares `torch`,
`einops`, `pytorch3d`, `invariant-point-attention`, `sidechainnet`,
`biopython`, `mp-nerf`, `mdtraj`, `proDy`, `transformers`, and related
scientific packages. A `ModuleNotFoundError` for `Bio`, `sidechainnet`,
`mp_nerf`, `pytorch3d`, or `invariant_point_attention` is an environment
problem, not a model-shape problem.

Start with a package-level check:

```bash
python -c "import alphafold2_pytorch, torch; print(alphafold2_pytorch.__file__, torch.__version__)"
python -m pip check
```

Use the project's supported Python/PyTorch combination and a compatible
PyTorch3D build. Do not hide a failed import by importing an internal class or by copying
source files into the application. The checked CPU environment imported
the package and ran tiny model calls; CUDA remained optional/unverified.

The external embedding wrappers in `alphafold2_pytorch/embeds.py` can import
Transformers and call `torch.hub` or Hugging Face downloads during wrapper
construction. Pretrained model downloads, Apex/fused operations, and network
access are outside the core smoke. Route those failures to
[embeddings](../../embeddings/SKILL.md).

## Invalid sequence, MSA, or mask dimensions

Use these shapes as the first diagnostic checklist:

```text
seq       (B, N)       integer token ids
msa       (B, M, N)    integer token ids
mask      (B, N)       boolean residue mask
msa_mask  (B, M, N)    boolean MSA mask
```

The source asserts `msa.shape[-1] == seq.shape[-1]`. A width mismatch produces
`sequence length of MSA and primary sequence must be the same`; fix the input
or pad/alignment preprocessing rather than following the README's old claim
that MSA width may differ.

For normal calls, pass `mask` and `msa_mask` explicitly. If `msa` is omitted,
the source creates `msa = seq[:, None, :]` and immediately rearranges `mask`;
`model(seq)` therefore fails when `mask=None`. The fallback derives
`msa_mask` from `mask`, so a separately supplied `msa_mask` does not control
that route. Ensure masks are boolean and share the input device.

A template call additionally needs:

```text
templates_feats   (B, T, N, N, templates_dim)
templates_angles  (B, T, N, templates_angles_feats_dim)
templates_mask    (B, T, N)
```

The source expects `templates_mask` whenever template features or angles are
used and does not provide friendly validation for a wrong final feature width.
A linear-layer `mat1 and mat2 shapes cannot be multiplied` error usually means
`templates_dim` or `templates_angles_feats_dim` does not match the constructor.

## Token embedding disablement

With `disable_token_embed=True`, the forward path raises one of these source
assertions unless both direct embedding tensors are supplied:

```text
sequence embedding must be supplied if one has disabled token embedding
msa embedding must be supplied if one has disabled token embedding
```

Provide `seq_embed` `(B, N, dim)` and `msa_embed` `(B, M, N, dim)`, or use
`M=1` with both `(B, N, dim)` and `(B, 1, N, dim)` for the sequence-only
fallback. The integer `seq`/`msa` tensors are still used for indexing/control;
disabling token embeddings does not remove the need to pass them.

Do not rely on `embedds` as an alternative workaround. Although it appears in
the signature and has an intended projected width `num_embedds`, the current
branch is unreachable after the source creates a fallback MSA. Use direct
`seq_embed`/`msa_embed` or the separately routed embedding wrappers.

## Output or unpacking errors

The core path returns a `ReturnValues` object, not the tuple shown in the README.
Use:

```python
ret = model(...)
distogram_logits = ret.distance
angle_logits = ret.theta_logits, ret.phi_logits, ret.omega_logits
```

The angle attributes exist only when `predict_angles=True` and have final widths
25, 13, and 25. `ret.theta`, `ret.phi`, and `ret.omega` are declared dataclass
fields but remain `None` in the inspected implementation.

`return_trunk=True` returns the `ReturnValues` object before coordinate
refinement when `predict_coords=True`; with `predict_coords=False` it does not
change the normal core return. `return_aux_logits=True` produces
`(coords, ret)` only in the coordinate path. For coordinates, confidence, or
recyclables, use [structure-and-recycling](../../structure-and-recycling/SKILL.md)
instead of guessing a core return type.

## Extra-MSA and template source defects

The `extra_msa` branch currently embeds `msa` instead of `extra_msa`. If the
extra MSA has a different row count, the supplied `extra_msa_mask` can expose a
broadcasting/reshape failure; even with matching shapes, the values are not
reliably the intended extra input. Keep a same-shape smoke only when this
limitation is acceptable, or patch/upgrade the source deliberately and rerun
verification.

README template examples use `templates_seq`, `templates_coors`, and
`templates_sidechains`, but those names are absent from the installed forward
signature. Prepare the feature tensors described in the API reference instead.

## Memory growth and device failures

The trunk constructs pair features `(B, N, N, dim)` and performs axial
attention; MSA attention adds an `(M, N)` axis. Memory grows rapidly with
sequence width, MSA rows, model depth, attention heads, and embedding width.
For diagnosis:

1. Set `model.eval()` and wrap inference in `torch.no_grad()`.
2. Start with `B=1`, `N<=8`, `M<=2`, `depth=1`, and a small `dim`/`dim_head`.
3. Reduce `M` and `N` before changing unrelated flags; avoid allocating
   templates or extra MSAs until the base route works.
4. Keep all tensors on one device and use `--device cpu` with
   `scripts/core_smoke.py` for the verified baseline.
5. Treat `max_seq_len` as a construction argument, not a proven hard runtime
   guard; the inspected forward path has no explicit length assertion.

CUDA being installed or visible is not a successful CUDA smoke. The prepared
host could not allocate a tiny CUDA run because the shared device was OOM; use
CPU or obtain a free GPU before diagnosing CUDA-specific failures.

## README/source drift and unsupported knobs

At this version, the README contains examples for constructor flags that are
not in the inspected signature, including `reversible`, `use_conv`, sparse,
linear, Kronecker, memory-compressed, and custom block options. The source has
`reversible.py` and `rotary.py`, but the public `Alphafold2` path does not wire
those modules through constructor flags. Do not add such keywords to a verified
call unless the installed package has materially changed and its signature and
behavior have been rechecked.

Other drift includes unequal-width MSA examples, tuple-unpacked outputs,
README-era structure/atom arguments, and real-valued distance prediction.
When a README recipe conflicts with `inspect.signature` or source control flow,
record the conflict and follow the installed source. A package upgrade requires
a fresh signature, source, and smoke review rather than silently reusing this
reference.
