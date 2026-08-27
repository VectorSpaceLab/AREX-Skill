# Model API Troubleshooting

Use this reference when OpenFold Python integration, config validation, checkpoint import, output conversion, metric calculation, or acceleration flags fail.

## Fast Triage

| Symptom | Likely cause | Fix or route |
| --- | --- | --- |
| `ModuleNotFoundError: attn_core_inplace_cuda` | Compiled attention extension is missing from the runtime import path. | Continue with safe config/parser/protein inspection; route build/path repair to `../installation-assets/`; skip model/kernel tests. |
| `Invalid model name` | Preset typo or unsupported preset in this OpenFold version. | Run `scripts/validate_config_preset.py --preset NAME --json`; choose a source-backed preset family. |
| `use_flash requires that FlashAttention is installed` | `globals.use_flash=True` without `flash_attn`. | Disable FlashAttention or route backend setup to `../installation-assets/`. |
| `use_deepspeed_evo_attention requires...` | DeepSpeed4Science Evoformer attention unavailable. | Disable the flag or install/validate DeepSpeed4Science. |
| `use_cuequivariance_xxx requires...` | cuEquivariance package unavailable. | Disable cuEquivariance flags or route backend setup to `../installation-assets/`. |
| `Only one of ... may be set` | Mutually exclusive attention/memory flags were combined. | Pick one of LMA, FlashAttention, DeepSpeed Evoformer attention, or cuEquivariance attention. |
| `AssertionError` during JAX weight import | NPZ keys do not match the requested model/version. | Match `version` and `model_config` preset family. |
| Missing or unexpected state-dict keys | Checkpoint wrapper, prefix, version, template, pTM, multimer, or SoloSeq mismatch. | Extract `state_dict`/`module`, retry v1 conversion path, and re-check preset family. |
| Shape mismatch in import or forward | Checkpoint architecture or batch feature family does not match config. | Rebuild config to match checkpoint/data; avoid manual tensor guesses. |
| `KeyError` in `AlphaFold.forward` | Batch lacks processed feature tensors. | Generate/process features through `../data-preparation/` or use public CLIs. |
| PDB output fails for many chains | PDB chain ID limit exceeded. | Use `protein.to_modelcif` instead of PDB. |

## Extension Import Failure

The current environment used during this sub-skill draft could import `openfold.config`, parser modules, and `openfold.np.protein`, but `openfold.model.model` and `openfold.utils.script_utils` failed because `attn_core_inplace_cuda` was missing. This means:

- Config preset validation without model construction can still be useful.
- Protein output helpers can still be inspected.
- Source-backed model signatures and helper names should not be described as live-verified until imports are repaired.
- Native model, kernel, DeepSpeed, cuEquivariance, and weight-import tests should be skipped unless the compiled extension and optional packages are available.

Run `scripts/inspect_openfold_api.py --json` after any environment repair to capture the new import state.

## Config Preset Problems

Start with a minimal config check:

```bash
python scripts/validate_config_preset.py --preset model_1_ptm --json
```

Then add one override at a time:

1. `--precision bf16` or another precision.
2. `--long-sequence-inference`.
3. `--trt-mode ... --trt-engine-dir ...`.
4. One optional attention/backend flag.

Common config mistakes:

- Combining FlashAttention with DeepSpeed Evoformer attention or cuEquivariance attention.
- Requesting long-sequence inference in train mode.
- Using a multimer preset with monomer features or weights.
- Using a SoloSeq preset without sequence-embedding features.
- Setting TensorRT mode without an explicit engine directory.
- Assuming config validation compiles TensorRT engines or verifies GPU readiness.

## Optional Backend Failures

Optional dependencies are validated early when their flags are enabled. Choose the smallest recovery path:

1. Disable the optional flag and keep the same preset.
2. Route installation/backend setup to `../installation-assets/`.
3. Route public CLI flag construction to `../inference/` or `../training/`.
4. Select hardware-sensitive native tests only after backend imports and device support are proven.

Do not install every optional backend by default. Match the backend set to the user's task.

## Batch and Tensor Issues

`AlphaFold.forward(batch)` is a low-level API. It expects processed tensors with a recycling dimension and mode-specific feature keys.

Common mistakes:

- Passing raw FASTA strings, raw parser outputs, raw alignment files, or raw mmCIF text directly to `forward`.
- Omitting template features while `config.model.template.enabled` is true.
- Using monomer features with a multimer config that expects `asym_id` and multimer semantics.
- Using SoloSeq config without `seq_embedding` features.
- Dropping the final recycling dimension during custom preprocessing.

Fix by using OpenFold feature pipelines or public CLI-generated feature outputs. Route data layout work to `../data-preparation/`.

## Checkpoint Mismatches

Classify before loading:

- AlphaFold/JAX `.npz`: use `import_jax_weights_` with matching `version`.
- OpenFold `.pt`: load on CPU and use `import_openfold_weights_` after model import works.
- PyTorch Lightning `.ckpt`: extract `checkpoint["state_dict"]`.
- DeepSpeed checkpoint directory: consolidate/convert first.
- Older OpenFold v1 checkpoint: use deprecated key conversion or v1-to-v2 conversion planning.
- OpenFold-to-JAX output request: require explicit output path and template NPZ.

If keys still mismatch, compare preset number, template enablement, pTM head, multimer family, SoloSeq mode, and any `module.`/`model.` prefixes before editing tensor names manually.

## Protein and Structure Output Issues

`protein.from_prediction` expects feature and result mappings, not raw model-less structures. Common fixes:

- Build per-atom B-factors when transferring pLDDT into PDB temperature factors.
- Check `remove_leading_feature_dimension=True` against actual feature array rank.
- Use ModelCIF when PDB cannot encode the chain count or metadata.
- Pass `parents` and `parents_chain_index` when template parent metadata should appear in outputs.

## Validation Metric Issues

Metric helpers do not align structures or choose atom subsets:

- Use `drmsd` for torch tensors and `drmsd_np` for numpy-starting arrays.
- Supply masks for padded residues or missing atoms.
- Compare like with like: CA-only to CA-only, all-atom to all-atom, same units.
- Do not compare directly to benchmark numbers unless preprocessing and alignment match the benchmark protocol.

## Safe Debugging Sequence

1. Run `scripts/inspect_openfold_api.py --json` to record package version, safe imports, signature availability, preset summaries, and optional backend state.
2. Run `scripts/validate_config_preset.py --preset PRESET --json` with no optional flags.
3. Add precision, long-sequence, TensorRT, and optional kernel flags one at a time.
4. Repair compiled-extension imports before claiming `AlphaFold` or `script_utils` live verification.
5. Classify checkpoint format before loading or converting.
6. Route feature generation and public command construction to sibling sub-skills instead of bypassing them with raw tensors.
