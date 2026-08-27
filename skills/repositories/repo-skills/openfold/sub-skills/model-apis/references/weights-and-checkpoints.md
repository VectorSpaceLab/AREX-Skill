# OpenFold Weights and Checkpoints

Use this reference to classify checkpoint formats and choose API-level import or conversion routes. Loading or converting large checkpoints can read/write substantial files and may require optional dependencies; keep this sub-skill focused on safe planning unless the user explicitly asks to execute in a prepared environment.

## Decision Tree

| Input or goal | Route | Why |
| --- | --- | --- |
| AlphaFold/JAX `.npz` parameters | Build a matching `model_config`/`AlphaFold`, then call `import_jax_weights_(model, npz_path, version=...)`. | Imports AlphaFold-format arrays into an OpenFold model. |
| OpenFold `.pt` or already-loaded PyTorch state dict | Extract the state dict and call `import_openfold_weights_(model, state_dict)`. | Loads current OpenFold keys and retries deprecated v1 key conversion. |
| PyTorch Lightning `.ckpt` wrapper | Load on CPU, extract `checkpoint["state_dict"]`, then call `import_openfold_weights_`. | Wrapper keys differ from a bare state dict. |
| DeepSpeed checkpoint directory | Consolidate/convert before normal OpenFold import. | Sharded DeepSpeed trees need the `latest` tag and zero-to-fp32 utilities. |
| Older OpenFold v1 checkpoint | Try `import_openfold_weights_` or plan v1-to-v2 conversion. | Current source includes deprecated key replacement logic. |
| Need a JAX `.npz` output from OpenFold weights | Plan OpenFold-to-JAX conversion with a template AlphaFold NPZ. | Conversion needs a matching OpenFold checkpoint, config preset, and template NPZ key set. |

## Programmatic Import APIs

Source-backed signatures:

- `import_jax_weights_(model, npz_path, version="model_1")`
- `import_openfold_weights_(model, state_dict)`

Example shape for trusted local files:

```python
from openfold.config import model_config
from openfold.model.model import AlphaFold
from openfold.utils.import_weights import import_jax_weights_, import_openfold_weights_

config = model_config("model_1_ptm")
model = AlphaFold(config)
import_jax_weights_(model, "params_model_1_ptm.npz", version="model_1_ptm")
```

Only use this after model imports succeed. In the current inspection environment, model imports fail until `attn_core_inplace_cuda` is available.

## Safe PyTorch Loading Pattern

For trusted OpenFold-native files:

```python
checkpoint = torch.load(checkpoint_path, map_location="cpu")
if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
    state_dict = checkpoint["state_dict"]
elif isinstance(checkpoint, dict) and "module" in checkpoint:
    state_dict = checkpoint["module"]
else:
    state_dict = checkpoint
import_openfold_weights_(model, state_dict)
```

Do not load untrusted `.pt` or `.ckpt` files without explicit user acceptance because PyTorch checkpoint loading uses pickle deserialization.

## JAX NPZ Import Notes

`import_jax_weights_` loads an `.npz`, generates a model-specific translation dictionary, checks that expected AlphaFold-format keys exist, and assigns transformed arrays into model parameters.

Common failures:

- `AssertionError` from missing expected NPZ keys: wrong `version`, wrong preset family, or incomplete parameter file.
- Tensor shape mismatch: checkpoint architecture does not match the constructed model.
- Multimer mismatch: `version` and preset must both belong to the multimer family.
- pTM mismatch: pTM heads require a pTM checkpoint family.

## OpenFold State Dict Notes

`import_openfold_weights_` first calls `model.load_state_dict(state_dict)`. If that raises `RuntimeError`, it converts deprecated v1 keys and retries. The source conversion covers template embedder renames and selected core/template/IPA key changes.

If loading still fails, collect:

- Config preset and whether `train`, template, pTM, multimer, or SoloSeq settings differ from the checkpoint source.
- Missing and unexpected key lists from the exception.
- Whether the checkpoint is bare OpenFold, Lightning, EMA, or DeepSpeed-derived.
- Whether keys contain `module.` or `model.` prefixes.
- Whether the file was converted from an older OpenFold release.

## DeepSpeed Checkpoint Conversion

The v1-to-v2 conversion utility treats directory inputs as DeepSpeed checkpoints:

- A directory input must contain a `latest` file naming the active checkpoint tag.
- It uses DeepSpeed zero-to-fp32 utilities to find optimizer/model state shards.
- It copies the checkpoint tree and rewrites converted key names.
- A file input is treated as a regular checkpoint and converted without DeepSpeed consolidation.

Choose this path only when the user has a checkpoint tree or old checkpoint that actually needs conversion. DeepSpeed installation and backend validation belong in `../installation-assets/`; training checkpoint provenance and resume behavior belong in `../training/`.

## OpenFold-to-JAX Conversion

The OpenFold-to-JAX conversion utility shape is:

```text
OF_CHECKPOINT.pt CONFIG_PRESET OUT_PARAMS.npz --template_npz_path TEMPLATE_SUPERSET_PARAMS.npz
```

Source behavior:

1. Load an OpenFold `.pt` checkpoint.
2. Build `model_config(config_preset)` and `AlphaFold(config)`.
3. Import OpenFold weights into the model.
4. Build the OpenFold-to-AlphaFold translation dictionary.
5. Load a template AlphaFold `.npz` with a superset of parameter keys.
6. Write a new AlphaFold-format `.npz`.

Do not rely on source-checkout default resource paths. Require explicit user paths for the OpenFold checkpoint, config preset, output file, and template NPZ.

## Checkpoint Request Classifier

When asked how to convert or load weights:

1. If the input is a directory with `latest`, classify it as a DeepSpeed checkpoint tree.
2. If the input is `.npz`, classify it as AlphaFold/JAX parameters and require a matching `version`/preset.
3. If the input is `.pt` or `.ckpt`, inspect wrapper keys safely and use `import_openfold_weights_` after model imports work.
4. If output is requested as `.npz`, plan OpenFold-to-JAX conversion with a template NPZ.
5. If missing/unexpected keys appear, re-check preset family before hand-editing keys.

## Safety and Routing

- Route model parameter downloads, large database acquisition, CUDA/PyTorch/DeepSpeed setup, and compiled extension repair to `../installation-assets/`.
- Route inference commands that consume checkpoints to `../inference/`.
- Route training checkpoint resume and experiment-state questions to `../training/`.
- Keep local checkpoint/cache paths out of public skill content and shared reports.
