# ESM-IF1 API Reference

This reference covers the inverse-folding APIs available in `fair-esm` 2.0.1 for sequence design and scoring from protein backbone coordinates.

## Model Loading

| API | Purpose | Notes |
| --- | --- | --- |
| `esm.pretrained.esm_if1_gvp4_t16_142M_UR50()` | Load the ESM-IF1 GVP Transformer and its alphabet. | Usually downloads weights through torch hub on first use. Call `model.eval()` before inference. |
| `esm.pretrained.load_model_and_alphabet("esm_if1_gvp4_t16_142M_UR50")` | Generic named model loader. | Equivalent path for named pretrained loading. |
| `esm.pretrained.load_model_and_alphabet_local(model_location)` | Load a local checkpoint file. | Use when weights are already available and network downloads are not allowed. |

Minimal setup:

```python
import esm
import esm.inverse_folding

model, alphabet = esm.pretrained.esm_if1_gvp4_t16_142M_UR50()
model = model.eval()
```

Move the model to CUDA only when the host has a compatible PyTorch/CUDA installation and enough memory:

```python
import torch

if torch.cuda.is_available():
    model = model.cuda()
```

## Single-Chain Coordinate APIs

| API | Signature | Returns | Use |
| --- | --- | --- | --- |
| `esm.inverse_folding.util.load_structure` | `load_structure(fpath, chain=None)` | `biotite.structure.AtomArray` filtered to backbone atoms and requested chains. | Read `.pdb` or `.cif` files and validate chain IDs. |
| `esm.inverse_folding.util.extract_coords_from_structure` | `extract_coords_from_structure(structure)` | `(coords, seq)` | Convert a loaded structure into N/CA/C coordinates and the extracted native sequence. |
| `esm.inverse_folding.util.load_coords` | `load_coords(fpath, chain)` | `(coords, seq)` | Convenience wrapper for one chain. |
| `model.sample` | `model.sample(coords, partial_seq=None, temperature=1.0, confidence=None, device=None)` | Sampled sequence string. | Generate a fixed-backbone design for one coordinate tensor. |
| `esm.inverse_folding.util.score_sequence` | `score_sequence(model, alphabet, coords, seq)` | `(ll_fullseq, ll_withcoord)` | Score one sequence against one coordinate tensor. |
| `esm.inverse_folding.util.get_encoder_output` | `get_encoder_output(model, alphabet, coords)` | Per-residue encoder representation tensor. | Extract structure-conditioned embeddings from ESM-IF1. |

Single-chain sampling example:

```python
import torch
import esm
import esm.inverse_folding

model, alphabet = esm.pretrained.esm_if1_gvp4_t16_142M_UR50()
model = model.eval()
coords, native_seq = esm.inverse_folding.util.load_coords("input.pdb", "C")
with torch.no_grad():
    sampled_seq = model.sample(coords, temperature=1.0, device="cpu")
```

Single-chain scoring example:

```python
coords, native_seq = esm.inverse_folding.util.load_coords("input.cif", "A")
ll_fullseq, ll_withcoord = esm.inverse_folding.util.score_sequence(
    model, alphabet, coords, native_seq
)
```

`ll_fullseq` is the average conditional log-likelihood over the full sequence. `ll_withcoord` excludes residues whose backbone coordinates are missing or masked.

## Multichain Complex APIs

| API | Signature | Returns | Use |
| --- | --- | --- | --- |
| `esm.inverse_folding.multichain_util.extract_coords_from_complex` | `extract_coords_from_complex(structure)` | `(coords, seqs)` dictionaries keyed by chain ID. | Convert a loaded complex into per-chain coordinate and sequence dictionaries. |
| `esm.inverse_folding.multichain_util.load_complex_coords` | `load_complex_coords(fpath, chains)` | `(coords, seqs)` dictionaries keyed by requested chain IDs. | Load a selected chain set when order matters. |
| `esm.inverse_folding.multichain_util.sample_sequence_in_complex` | `sample_sequence_in_complex(model, coords, target_chain_id, temperature=1.0, padding_length=10)` | Sampled target-chain sequence. | Design one target chain while conditioning on the full complex backbone. |
| `esm.inverse_folding.multichain_util.score_sequence_in_complex` | `score_sequence_in_complex(model, alphabet, coords, target_chain_id, target_seq, padding_length=10)` | `(ll_fullseq, ll_withcoord)` | Score a target sequence while conditioning on the full complex. |
| `esm.inverse_folding.multichain_util.get_encoder_output_for_complex` | `get_encoder_output_for_complex(model, alphabet, coords, target_chain_id)` | Target-chain representation tensor. | Extract target-chain encoder output with complex context. |

Multichain sampling example:

```python
import esm.inverse_folding

structure = esm.inverse_folding.util.load_structure("complex.pdb")
coords, native_seqs = esm.inverse_folding.multichain_util.extract_coords_from_complex(structure)
sampled_seq = esm.inverse_folding.multichain_util.sample_sequence_in_complex(
    model, coords, target_chain_id="C", temperature=1.0
)
```

Multichain scoring example:

```python
ll_fullseq, ll_withcoord = esm.inverse_folding.multichain_util.score_sequence_in_complex(
    model, alphabet, coords, target_chain_id="C", target_seq="MST..."
)
```

## Coordinate Batch Converter

`esm.inverse_folding.util.CoordBatchConverter(alphabet)` converts raw coordinate batches into tensors for low-level forward calls.

Raw item shape:

```python
(coords, confidence, seq)
```

- `coords`: length `L` array/list with shape `L x 3 x 3` for `N`, `CA`, and `C` atoms.
- `confidence`: `None`, a scalar, or a length-`L` confidence list.
- `seq`: length-`L` amino-acid string, or `None` to use placeholder residues.

Call forms:

```python
batch_converter = esm.inverse_folding.util.CoordBatchConverter(alphabet)
coords, confidence, strs, tokens, padding_mask = batch_converter(raw_batch, device="cpu")
coords, confidence, strs, tokens, padding_mask = batch_converter.from_lists(coords_list)
```

## Missing Coordinates

ESM-IF1 was trained to tolerate missing backbone coordinates. In arrays, missing or masked coordinate values are represented by non-finite values such as `np.nan` or `np.inf`.

```python
coords[:10, :] = float("inf")
```

Scoring reports both full-sequence log-likelihood and coordinate-present log-likelihood. Prefer `ll_withcoord` when comparing sequences for structures with missing or intentionally masked regions.
