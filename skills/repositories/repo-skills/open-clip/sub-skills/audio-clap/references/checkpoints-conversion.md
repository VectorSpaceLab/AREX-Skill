# Audio Checkpoints and HF CLAP Conversion

## Loading Audio Encoder Checkpoints

`AudioTower.load_pretrained_encoder(path, weights_only=True)` loads an audio encoder checkpoint onto `model.audio.encoder` with `strict=False`.

Behavior:

- Accepts raw state dicts or checkpoints with a `state_dict` key.
- Strips leading `module.` from keys.
- For Whisper towers, strips an `encoder.` prefix.
- For HTSAT-style towers, strips a `sed_model.` prefix.
- Returns the `load_state_dict` incompatible-key result so callers can inspect missing and unexpected keys.

`weights_only=True` is the safe default. The loader only retries with `weights_only=False` when PyTorch raises the specific weights-only unpickling error for non-tensor payloads. Treat that retry as a security-sensitive operation and only use it for trusted checkpoint files.

## Custom CLAP Zero-Shot Checkpoints

For custom CLAP or NaFlexClap checkpoints, use a trusted local evaluation wrapper that builds the exact OpenCLIP model, loads the checkpoint with explicit prefix handling, then calls `open_clip_train.audio_zero_shot.build_hf_audio_zero_shot_dataset()` and `audio_zero_shot_eval()`.

Common checkpoint loading decisions:

- Accept either a raw tensor state dict or a checkpoint with nested `state_dict`.
- Prefer `state_dict_ema` only when the checkpoint actually stores EMA weights and the evaluation policy calls for them.
- Strip common training prefixes such as `module.`, `_orig_mod.`, or `trainable_module.` before `model.load_state_dict(..., strict=False)`.
- Inspect missing/unexpected keys before trusting metrics.

Use `scripts/clap_zero_shot_args.py` to validate the intended model, dataset, keys, templates, and runtime flags before writing or running a custom checkpoint-loading wrapper.

## Transformers CLAP Conversion APIs

The audio conversion helpers live in `open_clip.audio.convert`:

```python
from open_clip.audio.convert import convert_hf_clap_state_dict, load_hf_clap_state_dict

converted = convert_hf_clap_state_dict(hf_state_dict)
converted_from_file = load_hf_clap_state_dict("checkpoint.safetensors")
```

`load_hf_clap_state_dict(path)` supports `.safetensors` through `safetensors.torch.load_file` and regular PyTorch checkpoints through `torch.load(..., weights_only=True)`. If the loaded object has `state_dict`, that nested mapping is converted.

## Key Mapping Summary

`convert_hf_clap_state_dict()` maps Transformers `ClapModel` keys to OpenCLIP CLAP keys.

Audio mappings include:

- `logit_scale_a` -> `logit_scale`. HF CLAP has directional scales; OpenCLIP CLAP uses one symmetric logit scale, and the converter maps the learned audio-to-text scale.
- `audio_model.audio_encoder.batch_norm.*` -> `audio.encoder.bn0.*`.
- `audio_model.audio_encoder.patch_embed.*` -> `audio.encoder.patch_embed.*`.
- `audio_model.audio_encoder.norm.*` -> `audio.encoder.norm.*`.
- `audio_model.audio_encoder.layers.*` -> `audio.encoder.layers.*`.
- HF query/key/value attention tensors are concatenated into `attn.qkv.weight` or `attn.qkv.bias` in query-key-value order.
- `audio_projection.linear1.*` -> `audio.proj.0.*`.
- `audio_projection.linear2.*` -> `audio.proj.2.*`.

Text mappings include:

- `text_model.*` -> `text.transformer.*`.
- `text_model.*.position_ids` and `text_model.*.token_type_ids` are dropped.
- `text_projection.linear1.*` -> `text.proj.0.*`.
- `text_projection.linear2.*` -> `text.proj.2.*`.

## Diagnosing Missing and Unexpected Keys

After conversion, load with `strict=False` first and inspect the incompatible keys:

```python
import open_clip
from open_clip.audio.convert import load_hf_clap_state_dict

model = open_clip.create_model(
    "CLAP-HTSAT-tiny-Roberta-base",
    pretrained=None,
    load_weights=False,
    pretrained_text=False,
)
converted = load_hf_clap_state_dict("hf-clap.safetensors")
incompatible = model.load_state_dict(converted, strict=False)
print("missing", incompatible.missing_keys[:20])
print("unexpected", incompatible.unexpected_keys[:20])
```

Expected missing keys for random/default Transformers CLAP-to-native tests include HTSAT attention masks and classification-head tensors such as `audio.encoder.tscam_conv.*` and `audio.encoder.head.*`. Unexpected keys should generally be empty for a matching OpenCLIP CLAP architecture.

Common mismatch causes:

- Loading an HTSAT HF CLAP checkpoint into a Whisper or NaFlexClap model.
- Using a model config whose text tower/projection type does not match HF CLAP `clap_mlp` projection shapes.
- Forgetting `pretrained_text=False` when instantiating a native model only to test state-dict conversion.
- Expecting both `logit_scale_a` and `logit_scale_t`; OpenCLIP receives only one `logit_scale`.
- Missing optional dependencies while building the target audio model before conversion.

Do not run conversion on user checkpoints automatically. First identify the source checkpoint family, instantiate the exact target OpenCLIP config, convert into CPU memory, and inspect missing/unexpected keys.
