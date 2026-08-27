# OpenFold Model API Reference

Use this reference for Python-level OpenFold integration. The API facts are source-backed from OpenFold 2.2.0 code and prior inspection, but the current private environment cannot import `openfold.model.model` or `openfold.utils.script_utils` until `attn_core_inplace_cuda` is available. Re-run `../scripts/inspect_openfold_api.py --json` in the target environment before claiming model import verification.

## Safe Imports First

These imports are safe to try before model construction:

```python
from openfold.config import model_config
from openfold.np import protein
from openfold.utils import validation_metrics
```

Model and script utility imports can transitively require compiled extensions:

```python
from openfold.model.model import AlphaFold
from openfold.utils.import_weights import import_jax_weights_, import_openfold_weights_
```

If those fail with `ModuleNotFoundError: attn_core_inplace_cuda`, route compiled-extension repair to `../installation-assets/` and continue with safe config/parser/protein inspection where possible.

## Config and Model Construction

Preferred construction path:

```python
config = model_config("model_1_ptm", train=False, precision="tf32")
model = AlphaFold(config)
```

Source-backed signatures:

- `openfold.config.model_config(name, train=False, low_prec=False, long_sequence_inference=False, use_deepspeed_evoformer_attention=False, use_cuequivariance_attention=False, use_cuequivariance_multiplicative_update=False, precision="tf32", trt_mode=None, trt_engine_dir=None, trt_num_profiles=1, trt_optimization_level=3, trt_max_sequence_len=640)`
- `openfold.model.model.AlphaFold.__init__(self, config)`
- `openfold.model.model.AlphaFold.forward(self, batch)`

`model_config` returns an `ml_collections.ConfigDict`-style object consumed by `AlphaFold`. It applies preset-specific changes and enforces selected backend constraints before returning.

## `AlphaFold.forward(batch)` Inputs

`AlphaFold.forward(batch)` consumes processed feature tensors, not raw FASTA, raw MSA files, raw parser records, or raw mmCIF text. Raw data and feature generation belong in `../data-preparation/`; public prediction command construction belongs in `../inference/`.

Important batch caveats from the model source:

- The final dimension of batch features is used for recycling iterations.
- Core keys include `aatype`, `target_feat`, `residue_index`, `seq_mask`, `msa_feat`, `msa_mask`, `pair_mask`, and `extra_msa_mask` depending on mode.
- Template-enabled configs need template features such as `template_mask`, `template_aatype`, `template_all_atom_positions`, `template_all_atom_mask`, `template_pseudo_beta`, `template_pseudo_beta_mask`, and template torsion fields for monomer template paths.
- Multimer configs use multimer-specific features such as `asym_id`; outputs can preserve `asym_id`.
- SoloSeq/sequence-embedding presets expect `seq_embedding` features rather than ordinary MSA assumptions.

Avoid hand-authoring synthetic tensors for real model runs unless the task is explicitly testing model internals. Prefer OpenFold feature processors, CLI-produced features, or native fixtures.

## Model Outputs and Structure Conversion

Prediction output conversion is handled by `openfold.np.protein`:

```python
prot = protein.from_prediction(features, result, b_factors=None)
pdb_text = protein.to_pdb(prot)
modelcif_text = protein.to_modelcif(prot)
```

Source-backed signatures:

- `openfold.np.protein.from_prediction(features, result, b_factors=None, remove_leading_feature_dimension=True, remark=None, parents=None, parents_chain_index=None)`
- `openfold.np.protein.to_pdb(prot)`
- `openfold.np.protein.to_modelcif(prot)`

`Protein` stores atom positions, amino-acid type indices, atom masks, residue indices, B-factors, optional chain indices, optional remarks, and optional parent-template metadata. `from_prediction` uses `features["asym_id"] - 1` as chain indices when `asym_id` exists; otherwise it emits a single-chain structure. It increments `residue_index` for PDB-style numbering.

PDB output has a hard 62-chain limit. Prefer ModelCIF for large complexes, richer metadata, or outputs whose chain count may exceed PDB limits.

## Weight Import APIs

Source-backed signatures:

- `openfold.utils.import_weights.import_jax_weights_(model, npz_path, version="model_1")`
- `openfold.utils.import_weights.import_openfold_weights_(model, state_dict)`

Use `import_jax_weights_` when loading AlphaFold-format JAX `.npz` arrays into a constructed OpenFold model. The `version` argument must match the preset family, such as `model_1`, `model_1_ptm`, or a multimer preset.

Use `import_openfold_weights_` when the caller already has an OpenFold/PyTorch state dict. It first calls `model.load_state_dict(state_dict)`, then retries with deprecated v1 key conversion if direct loading raises `RuntimeError`.

Safe CPU load pattern for caller-owned checkpoint files:

```python
checkpoint = torch.load(checkpoint_path, map_location="cpu")
state_dict = checkpoint.get("state_dict", checkpoint.get("module", checkpoint))
import_openfold_weights_(model, state_dict)
```

PyTorch checkpoint loading can execute pickle deserialization; do not load untrusted `.pt` or `.ckpt` files without explicit user acceptance.

## Validation Metrics

Source-backed metric helpers:

- `validation_metrics.drmsd(structure_1, structure_2, mask=None)`
- `validation_metrics.drmsd_np(structure_1, structure_2, mask=None)`
- `validation_metrics.gdt(p1, p2, mask, cutoffs)`
- `validation_metrics.gdt_ts(p1, p2, mask)`
- `validation_metrics.gdt_ha(p1, p2, mask)`

These functions operate on prepared coordinate tensors/arrays plus masks. They do not load structures, select atom subsets, superpose structures, or reproduce benchmark preprocessing automatically. Align atom selection, padding masks, and units before comparing values.

## Script Utility APIs

Source-backed utility names used by public CLIs include:

- `openfold.utils.script_utils.load_models_from_command_line(config, model_device, openfold_checkpoint_path, jax_param_path, output_dir)`
- `openfold.utils.script_utils.run_model(model, batch, tag, output_dir)`
- `openfold.utils.script_utils.prep_output(out, batch, feature_dict, feature_processor, config_preset, multimer_ri_gap, subtract_plddt)`
- `openfold.utils.script_utils.relax_protein(config, model_device, unrelaxed_protein, output_directory, output_name, cif_output=False)`

In the current environment these imports fail with the same missing compiled attention extension as the model import. Prefer public CLIs for normal prediction flows; use these helpers only when building a custom Python integration around already-prepared features and outputs.

## Focused Native Test Guidance

Select native tests only after whole-skill integration and environment readiness checks:

| Goal | Candidate | Default stance |
| --- | --- | --- |
| Basic config/parser import smoke | Safe import smoke around `openfold.config`, parser modules, and `openfold.np.protein` | Good lightweight default. |
| Model construction/forward compatibility | Maintainer model tests | Requires repaired model imports and may be compute-heavy. |
| JAX/OpenFold weight translation | Maintainer import-weight tests | Prefer small fixtures; avoid large real checkpoints unless approved. |
| Custom kernel parity | Maintainer kernel tests | Requires compiled kernels and hardware alignment. |
| DeepSpeed Evoformer attention parity | Maintainer DeepSpeed attention tests | Optional-package and hardware sensitive. |
| cuEquivariance attention/update behavior | Maintainer cuEquivariance tests | Optional-package and hardware sensitive. |
