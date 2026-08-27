# Model Weights

## Purpose

Use this reference when RFdiffusion commands require checkpoint files, model directories, or checkpoint overrides. This generated skill does not download weights automatically because official weights are large network artifacts.

## Required Checkpoint Files

RFdiffusion documentation names these common files:

| File | Typical use |
| --- | --- |
| `Base_ckpt.pt` | Default monomer/unconditional and many motif workflows. |
| `Complex_base_ckpt.pt` | Complex or target-aware motif and binder workflows. |
| `Complex_Fold_base_ckpt.pt` | Fold-conditioned complex workflows where available. |
| `InpaintSeq_ckpt.pt` | Sequence/structure inpainting workflows. |
| `InpaintSeq_Fold_ckpt.pt` | Fold-conditioned inpainting workflows. |
| `ActiveSite_ckpt.pt` | Very small active-site or enzyme motifs that need stronger motif retention. |
| `Base_epoch8_ckpt.pt` | Some documented symmetric motif/nickel-style tasks. |
| `Complex_beta_ckpt.pt` | Optional beta complex checkpoint documented by the repo. |
| `RF_structure_prediction_weights.pt` | Original structure-prediction weights, not a normal diffusion inference checkpoint. |

## How Commands Find Weights

Prefer passing a model directory explicitly when the runtime install does not have a conventional models directory:

```bash
run_inference.py \
  inference.model_directory_path=/path/to/models \
  'contigmap.contigs=[100-100]' \
  inference.output_prefix=outputs/design
```

Use `inference.ckpt_override_path=/path/to/models/ActiveSite_ckpt.pt` only when the workflow explicitly calls for a non-default checkpoint.

## Checkpoint Selection Hints

- Use the default base behavior for ordinary unconditional monomers.
- Use active-site checkpoint overrides for tiny functional motifs or enzyme active-site scaffolding.
- Use complex checkpoint overrides when a fixed target/receptor chain is central to motif scaffolding or binder generation and RFdiffusion does not auto-select the desired complex model.
- Inpaint sequence/structure options can trigger inpaint-capable checkpoint selection; avoid overriding unless the workflow evidence requires it.
- Symmetric nickel-like examples may use `Base_epoch8_ckpt.pt`.

## Safe Validation

Run the root environment checker before inference:

```bash
python scripts/check_rfdiffusion_environment.py --models /path/to/models --require Base_ckpt.pt --require ActiveSite_ckpt.pt
```

The checker only verifies importability and file presence; it does not validate scientific suitability or run RFdiffusion sampling.

## Troubleshooting

- If RFdiffusion cannot find a checkpoint, pass `inference.model_directory_path` or an explicit `inference.ckpt_override_path`.
- If an override crashes with config/key mismatches, check that the checkpoint matches the selected workflow features.
- If the first run stalls at IGSO3 calculation, distinguish normal first-run schedule caching from a missing checkpoint or GPU memory failure.
- If a user asks to download weights, provide the public RFdiffusion documentation commands in their environment, but do not run network downloads unless explicitly requested and safe.
