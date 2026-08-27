# Hub and Conversion Interoperability

This reference covers timm model loading from Hugging Face Hub or local directories, model publication helpers, Torch Hub compatibility, and conversion-script boundaries.

## Hugging Face Hub Loading

`timm.create_model` parses model names with source prefixes. For Hub-hosted models, use the `hf-hub:` scheme:

```python
import timm

model = timm.create_model('hf-hub:timm/resnet18.a1_in1k', pretrained=True)
```

A revision can be appended with `@revision`:

```python
model = timm.create_model('hf-hub:org/model-name@main', pretrained=True)
```

Important behavior:

- `hf-hub:` loading requires `huggingface_hub`; timm raises an installation-focused error if it is missing.
- The Hub repository must provide `config.json`; timm parses `architecture`, `pretrained_cfg`, optional `model_args`, and label metadata from it.
- When `safetensors` is installed, timm prefers safe weight alternatives such as `model.safetensors` before falling back to PyTorch weight files.
- `cache_dir` can be passed through `create_model(..., cache_dir=...)` to override the Hugging Face and checkpoint cache location for that load.
- For custom loaders with Hub filenames, timm can use `hf_hub_filename` from pretrained config and dispatch to custom loading when configured.

## Local Directory Loading

Local directory loading uses the `local-dir:` scheme and the same `config.json` structure used for Hub packages:

```python
import timm

model = timm.create_model('local-dir:/models/my-timm-model', pretrained=True)
```

The directory must contain:

- `config.json` with at least the model `architecture` and a `pretrained_cfg` block.
- A recognized weight file. Preferred names include `model.safetensors`, `pytorch_model.bin`, `pytorch_model.pth`, `model.pth`, `open_clip_model.safetensors`, and OpenCLIP PyTorch variants. Fallback search covers `.safetensors`, `.pth`, `.pth.tar`, and `.bin` files.

If more than one fallback file exists for an extension, timm selects the first sorted file and logs a warning. For reliable packaging, use one preferred weight filename rather than relying on fallback discovery.

## Publishing to the Hub

`timm.models.push_to_hf_hub` saves model weights and config to a temporary package, creates or reuses a Hub repo, optionally writes a README model card, and uploads the folder.

Minimal pattern:

```python
import timm

model = timm.create_model('resnet18', pretrained=True, num_classes=4)
model_config = {'label_names': ['cat', 'dog', 'car', 'tree']}
timm.models.push_to_hf_hub(model, 'username/resnet18-custom', model_config=model_config)
```

Key arguments:

| Argument | Purpose | Guidance |
| --- | --- | --- |
| `repo_id` | Hub repository id | Use `owner/name` for deterministic ownership. |
| `token` | Authentication token | Prefer environment or login-managed auth; do not hardcode tokens. |
| `revision` | Branch/revision target | Use when publishing to a branch or pull request. |
| `private` | Create private repo | Use for non-public or licensed weights. |
| `create_pr` | Upload as pull request | Useful for controlled model updates. |
| `model_config` | Extra config fields | Include label metadata, class count, or other consumer-relevant values. |
| `model_args` | Constructor args for reload | Include args needed to recreate custom model variants. |
| `model_card` | README metadata | Include license, datasets, tags, usage, comparison, and citation when available. |
| `safe_serialization` | Weight serialization mode | Default is both safe and PyTorch formats; use `True` for safetensors-only publication. |

`save_for_hf` writes `config.json` plus `model.safetensors` and/or `pytorch_model.bin` depending on `safe_serialization`. Prefer safetensors for public distribution and include PyTorch weights only when legacy consumers require them.

## Torch Hub Compatibility

`timm` exposes a minimal `hubconf.py` with `dependencies = ['torch']` and registers timm model entrypoints into the Torch Hub namespace. This supports legacy flows such as `torch.hub.load` against a repository checkout or GitHub source.

Practical guidance:

- Prefer direct `import timm; timm.create_model(...)` for new code because it exposes tags, pretrained configs, `cache_dir`, and source prefixes more clearly.
- Use Torch Hub only when the consuming environment requires the Torch Hub API.
- Torch Hub may need a repository checkout or network access depending on how it is invoked.
- Torch Hub entrypoints are model constructors; model-name discovery and pretrained tag handling are easier through timm's public model-library APIs.

## Conversion Scripts Are Reference-Only

The `convert/` scripts are useful evidence for how maintainers translate external checkpoints into timm-compatible state dicts, but they are not general-purpose bundled tools.

Observed conversion categories:

| Script category | External dependency pattern | Caveat |
| --- | --- | --- |
| MXNet conversion | MXNet checkpoint and MXNet runtime conventions | Requires external framework/package and source checkpoint naming. |
| Flax/JAX conversion | Flax/JAX parameter structures | Requires architecture-specific parameter mapping. |
| Gemma/Vision conversion | Specialized upstream model checkpoints | Requires upstream checkpoint format and model-specific mapping logic. |

When asked to convert external weights:

1. Identify the source framework, checkpoint format, and exact architecture variant.
2. Check whether timm already has a matching architecture and pretrained config.
3. Adapt only the relevant mapping logic into a project-local conversion script.
4. Validate by loading the converted state dict into `timm.create_model(..., pretrained=False)` with expected missing/unexpected keys.
5. Clean the converted checkpoint with the checkpoint workflow before sharing.

Do not present conversion as a guaranteed one-command flow unless the external framework, checkpoint files, exact mapping, and validation target are all available.
