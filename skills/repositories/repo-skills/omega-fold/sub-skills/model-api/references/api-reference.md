# OmegaFold API Reference

This reference covers the public Python API and the adjacent helpers an agent usually needs for custom inference. It is self-contained and avoids weight downloads unless explicitly requested by the caller.

## Imports and Package Facts

```python
import argparse
import torch
import omegafold
from omegafold import confidence, pipeline
```

Installed metadata may report distribution name `OmegaFold` and version `0.0.0`. The import module is `omegafold`. Public root exports include `omegafold.make_config` and `omegafold.OmegaFold`; helpers live under `omegafold.pipeline` and `omegafold.confidence`.

## Configs

Signature:

```python
cfg = omegafold.make_config(model_idx: int = 1)
```

Valid `model_idx` values are `1` and `2`. Any other id raises `ValueError("model_idx must be 1 or 2")`.

Important fields returned on the `argparse.Namespace` config:

| Field | Typical value | Use |
| --- | ---: | --- |
| `alphabet_size` | `21` | Residue token vocabulary used outside the PLM. |
| `plm.alphabet_size` | `23` | OmegaPLM token vocabulary. |
| `plm.node` | `1280` | Raw PLM node embedding size projected to `node_dim`. |
| `plm.edge` | `66` | Raw PLM edge embedding size projected to `edge_dim`. |
| `node_dim` | `256` | Main residue representation width. |
| `edge_dim` | `128` | Pair representation width. |
| `geo_num_blocks` | `50` | GeoFormer block count. |
| `struct.node_dim` | `384` | Structure module node width. |
| `struct.num_cycle` | `8` | Internal structure-module cycle parameter. |
| `struct.num_bins` | `50` | Confidence head pLDDT bins. |
| `struct_embedder` | `False` for model 1, `True` for model 2 | Main config difference exposed by `make_config`. |

Use model 2 only with model 2 weights. Its config turns on `struct_embedder`; using model 1 weights with model 2 or the reverse can produce missing/unexpected key errors or wrong behavior.

## Model Construction

Signature:

```python
model = omegafold.OmegaFold(cfg)
```

`OmegaFold` is a `torch.nn.Module`. Construction allocates the model modules but does not download or load weights. Instantiating can still use substantial memory because the release model includes OmegaPLM, GeoFormer, structure, recycle, and confidence components.

Common setup:

```python
cfg = omegafold.make_config(1)
model = omegafold.OmegaFold(cfg)
state_dict = torch.load("model.pt", map_location="cpu")
state_dict = state_dict.get("model", state_dict)
model.load_state_dict(state_dict)
model.eval().to(device)
```

Prefer loading weights onto CPU first, then moving the model to the target device. If you need OmegaFold's default cache/download behavior, call `pipeline._load_weights(weights_url, weights_file)` explicitly; it downloads when `weights_file` is absent and `weights_url` is non-empty. For offline or reproducible usage, pass a local weights path and avoid URL downloads.

## Forward Inputs

Signature:

```python
output = model(
    inputs,
    predict_with_confidence=True,
    fwd_cfg=argparse.Namespace(subbatch_size=None, num_recycle=10),
)
```

`inputs` is a list of cycle dictionaries, usually produced by `pipeline.fasta2inputs`. Each cycle dictionary contains:

| Key | Shape idea | Meaning |
| --- | --- | --- |
| `p_msa` | `[num_pseudo_msa + 1, num_res]` | Tokenized pseudo-MSA; first row is the original sequence. |
| `p_msa_mask` | `[num_pseudo_msa + 1, num_res]` | Boolean/float mask; masked positions use token `21`. |

`fwd_cfg` is optional but should usually include:

| Field | Use |
| --- | --- |
| `subbatch_size` | Shards expensive attention/pair work to reduce GPU memory; `None` means no manual subbatch override. |
| `num_recycle` | Number of FASTA input cycles prepared by the CLI flow; commonly mirrors `--num_cycle`. |

`pipeline.fasta2inputs(fasta_path, output_dir=None, num_pseudo_msa=15, device=torch.device("cpu"), mask_rate=0.12, num_cycle=10, deterministic=True)` yields `(input_data, save_path)` pairs. It uppercases sequences, maps `Z->E`, `B->D`, `U->C`, uses `-` as mask token `21`, sorts entries by sequence length, and raises an assertion for unsupported amino-acid tokens. See the data/output sub-skill for detailed FASTA and PDB handling.

## Forward Outputs

`OmegaFold.forward` returns the selected cycle result dictionary. The key outputs used by the release CLI are:

| Key | Shape idea | Use |
| --- | --- | --- |
| `final_atom_positions` | `[num_res, 14, 3]` | Atom14 coordinates used for PDB writing. |
| `confidence` | `[num_res]` | Per-residue pLDDT-like confidence in `0..1`; CLI writes `confidence * 100` into PDB B-factors. |
| `confidence_overall` | Python `float` | Overall confidence selected from per-residue confidence and CA distances. |
| `final_frames` | internal frame object | Used for recycling; not normally serialized by API callers. |

When `predict_with_confidence=True`, OmegaFold tracks the cycle with the best `confidence_overall` and returns that result. When `False`, it returns the last cycle result.

## Internal API Hooks

These methods are useful for inspection and debugging, but they are not stable high-level APIs:

```python
node_repr, edge_repr = model.deep_sequence_embed(p_msa, p_msa_mask, fwd_cfg)
prev = model.create_initial_prev_dict(num_res)
```

`deep_sequence_embed` runs OmegaPLM, normalizes/project PLM node and edge representations, and applies input edge embedding. `create_initial_prev_dict(num_res)` creates zeroed `prev_node`, `prev_edge`, `prev_x`, and default `prev_frames` tensors on `model.device`. Use these for debugging shape problems, not as a separate feature-extraction contract unless you control the OmegaFold version.

## Confidence Helpers

`confidence.get_all_confidence(lddt_per_residue, ca_coordinates, ca_mask, cutoff=15.0) -> float` computes an overall confidence from per-residue lDDT-like scores and CA coordinates. Required shapes are:

- `lddt_per_residue`: one-dimensional `[num_res]` tensor.
- `ca_coordinates`: two-dimensional `[num_res, 3]` tensor.
- `ca_mask`: one-dimensional `[num_res]` tensor on the same device.

The confidence head internally maps logits to per-residue pLDDT-like values in `0..1`. The CLI multiplies these by `100` when storing them as PDB B-factors.

## Minimal Safe Inspection

Run this bundled script instead of importing source files manually:

```bash
python sub-skills/model-api/scripts/inspect_model_api.py
python sub-skills/model-api/scripts/inspect_model_api.py --check-invalid-model
python sub-skills/model-api/scripts/inspect_model_api.py --instantiate
```

`--instantiate` constructs `OmegaFold(cfg)` but still does not load weights or download anything. Use it only on a machine with enough RAM for model allocation.
