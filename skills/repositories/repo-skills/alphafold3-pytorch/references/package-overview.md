# Package overview

## When to read

Read this reference before choosing a route for a new AlphaFold 3 PyTorch task,
when checking what the package actually exposes, or when separating a bounded
API smoke test from a checkpoint/data-dependent run.

## Verified package identity

- Distribution: `alphafold3-pytorch`, version `0.8.3` at the source snapshot used
  for this skill.
- Import root: `alphafold3_pytorch`.
- Python metadata declares Python `>=3.9`, PyTorch `>=2.1`, and a broad scientific
  runtime including Biopython, Gemmi, RDKit, `pdbeccdutils`, Polars, Lightning,
  Transformers, and Gradio. Install the public distribution rather than
  reconstructing this list manually unless a deployment needs a pinned variant.
- Console entry points: `alphafold3_pytorch` maps to the Click CLI and
  `alphafold3_pytorch_app` maps to the local Gradio app.

## Capability map

| Task signal | Primary objects or modules | Route |
|---|---|---|
| Forward pass, diffusion, confidence, ranking, checkpoint | `Alphafold3`, `Alphafold3WithHubMixin`, architecture modules | `model-inference` |
| Sequence/chemical entities and atom features | `Alphafold3Input`, `MoleculeInput`, `AtomInput`, batching/conversion helpers | `input-representation` |
| Structure files, alignments, templates, crop/sampling | `PDBInput`, `PDBDataset`, `PDBDistillationDataset`, `alphafold3_pytorch.data` | `data-pipeline` |
| Training and YAML | `Trainer`, `DataLoader`, `Alphafold3Config`, `TrainerConfig`, `ConductorConfig` | `training-configuration` |
| Shell operation and UI | Click entry points, `app.py`, Gradio entity state/cache | `cli-serving` |

## Model/input boundary

`Alphafold3Input` is the high-level heterogeneous description. The package
transforms it into molecule-level and then atom-level features, and collates
those features into `BatchedAtomInput` for the model. The model's direct
`forward` path expects already prepared tensors and masks; it does not fetch
PDB, MSA, or template data.

For inference through `forward_with_alphafold3_inputs`, pass a high-level input
and use sampling-oriented options. For direct `forward`, distinguish these
modes:

- Training/loss mode requires the relevant coordinate and label tensors.
- Sampling mode uses `num_sample_steps` and omits training-only labels; it
  returns atom coordinates or requested structure/logit tuples.
- `return_loss=False` is useful for explicit sampling/diagnostic calls; the
  exact combinations of `return_confidence_head_logits`,
  `return_distogram_head_logits`, and structure-return flags are documented in
  the model route.

The constructor requires `dim_atom_inputs` and `dim_template_feats`; reduced
smoke models must also make compatible choices for the pair, token, MSA,
attention, and diffusion dimensions. Production defaults are intentionally
large.

## Data and environment boundary

PDB-derived atomization may need a Chemical Component Dictionary and its cached
SMILES mapping. The current package's data workflow uses a caller-controlled
`data/ccd_data` layout relative to the process working directory; provision and
validate that data before PDB/atomized-residue conversion. Do not treat the
package import alone as proof that CCD-backed conversion is ready.

MSA/template directories, Kalign, PDB cluster caches, external checkpoints,
and PDB/AFDB downloads are separate prerequisites. The `data-pipeline` route
contains safe preflight guidance and explicit acquisition stop conditions.

## Minimal public smoke

```bash
python - <<'PY'
import torch
import alphafold3_pytorch as af3
print(af3.__file__)
print(torch.__version__, torch.cuda.is_available())
print(af3.Alphafold3Input(proteins=['AG']))
PY
```

This checks import and high-level input construction only. It does not prove a
checkpoint, CUDA kernel path, or biological prediction quality.
