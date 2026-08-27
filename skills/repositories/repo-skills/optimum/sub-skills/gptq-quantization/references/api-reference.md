# Optimum GPTQ API reference

This reference summarizes the Optimum GPT-QModel API surfaces verified from source, docs, tests, and installed-package inspection. Use the installed package at runtime; do not depend on the source checkout.

## Public imports

```python
from optimum.gptq import GPTQQuantizer, load_quantized_model
from optimum.gptq.utils import get_seqlen, get_block_name_with_pattern, get_preceding_modules
from optimum.gptq.data import get_dataset, prepare_dataset, collate_data
```

`GPTQQuantizer` may import successfully even when `gptqmodel` is absent, but constructing the quantizer requires GPT-QModel classes. Always probe first with the bundled script.

## `GPTQQuantizer` constructor

Signature:

```python
GPTQQuantizer(
    bits: int,
    dataset=None,
    group_size: int = 128,
    damp_percent: float = 0.1,
    desc_act: bool = False,
    act_group_aware: bool = True,
    sym: bool = True,
    true_sequential: bool = True,
    model_seqlen=None,
    block_name_to_quantize=None,
    module_name_preceding_first_block=None,
    batch_size: int = 1,
    pad_token_id=None,
    cache_block_outputs: bool = True,
    modules_in_block_to_quantize=None,
    format: str = "gptq",
    meta=None,
    backend=None,
    *args,
    **kwargs,
)
```

| Field | Meaning and operating notes |
| --- | --- |
| `bits` | Target weight bit-width. Supported values are `2`, `3`, `4`, and `8`; other values raise `ValueError`. |
| `dataset` | Calibration data. Use a list of strings, a list of tokenized dictionaries with `input_ids` and `attention_mask`, or built-in dataset name `"wikitext2"`, `"c4"`, or `"c4-new"`. Required by `quantize_model`. |
| `group_size` | Quantization group size. Default `128`; `-1` means per-column quantization. Values other than `-1` must be positive. |
| `damp_percent` | Hessian dampening fraction. Default `0.1`; must satisfy `0 < damp_percent < 1`. |
| `desc_act` | Whether to quantize columns in decreasing activation-size order, also called act-order. May improve quality but can affect speed/compatibility. |
| `act_group_aware` | Group-aware activation order option. Applicable when `desc_act=False`; when using act-order, set this to `False` unless you have evidence the backend supports the combination. |
| `sym` | Use symmetric quantization. Default `True`. The default `gptq` v1 compatibility path is oriented around symmetric checkpoints. |
| `true_sequential` | If `True`, quantize sequentially inside each Transformer block. If `False`, quantize each configured group together. |
| `model_seqlen` | Maximum sequence length for calibration. Automatic inference reads common Transformers config fields; custom models should set this explicitly. |
| `block_name_to_quantize` | Dotted module path to the Transformer block list. Automatic discovery uses common patterns; custom models should set it. |
| `module_name_preceding_first_block` | Dotted module names that must run before the first block during calibration input capture. Important for custom architectures. |
| `batch_size` | Calibration batch size. Default `1`. If greater than `1`, `pad_token_id` is required. |
| `pad_token_id` | Padding token id used by dataset collation for batched calibration. |
| `cache_block_outputs` | Cache each block's outputs for reuse as succeeding block inputs. Default `True`; setting `False` recomputes block inputs and can be useful for memory/model-specific behavior. |
| `modules_in_block_to_quantize` | Optional list of lists of layer names relative to each block. Each inner list is quantized together/sequentially depending on `true_sequential`. Use it to exclude or order specific linear layers. |
| `format` | GPTQ weight format. Default `"gptq"` for broad compatibility. Optimum may use GPT-QModel's newer internal format during quantization and convert at save time. |
| `meta` | Optional metadata dictionary. `to_dict()` adds quantizer version tags under `meta["quantizer"]` when absent. |
| `backend` | Optional GPT-QModel kernel backend selector. Leave unset or use `"auto"` unless the user has a specific supported backend override. |

The constructor also sets `quant_method` to GPTQ and builds a GPT-QModel `QuantizeConfig` with `offload_to_disk=False`.

## Serialization keys

`GPTQQuantizer.to_dict()` serializes these keys into `quantize_config.json`:

```text
bits, dataset, group_size, damp_percent, desc_act, act_group_aware, sym,
true_sequential, quant_method, modules_in_block_to_quantize, format, meta
```

Runtime-only fields such as `model_seqlen`, `block_name_to_quantize`, `module_name_preceding_first_block`, `batch_size`, `pad_token_id`, `cache_block_outputs`, and `backend` are not emitted by the default `to_dict()` path. `GPTQQuantizer.from_dict()` passes all dictionary keys through to the constructor, so a custom workflow may add recognized constructor keys to a local `quantize_config.json` when automatic load-time inference is not sufficient. Keep such edits explicit and document why they were needed.

## Methods

### `quantize_model(model, tokenizer=None)`

Quantizes a model using the configured calibration dataset.

Behavior to account for:

- Requires `gptqmodel>=7.0.0`; otherwise raises a runtime dependency error or fails construction earlier.
- Sets `model.eval()` and temporarily disables `model.config.use_cache` when present.
- Rejects `hf_device_map` entries containing `"disk"` because disk offload is not supported during GPTQ quantization.
- Expects a text model/tokenizer path. A tokenizer can be an object, a tokenizer model id string, or a local tokenizer directory. Non-text models are not supported by this integration.
- Docs and tests load models as `torch.float16`; treat float16 as required for quantization planning.
- If `model_seqlen` is unset, uses `min(4028, get_seqlen(model))`.
- If `block_name_to_quantize` is unset, uses `get_block_name_with_pattern(model)`.
- If `module_name_preceding_first_block` is unset, uses `get_preceding_modules(model, block_name_to_quantize)`.
- Replaces quantized linear/Conv1D/Conv2d layers, packs them, marks the model as quantized, and attaches GPTQ quantization metadata to `model.config` when a config exists.

### `save(model, save_dir, max_shard_size="10GB", safe_serialization=True)`

Creates `save_dir` if needed, saves model weights/config through `model.save_pretrained`, and writes `quantize_config.json` with `to_dict()`.

Default `safe_serialization=True` writes safetensors-style files when supported by the model. If a single tensor exceeds `max_shard_size`, Transformers may place it in a larger shard.

### `load_quantized_model(...)`

Signature:

```python
load_quantized_model(
    model,
    save_folder: str,
    backend: str = "auto",
    quant_config_name: str = "quantize_config.json",
    state_dict_name=None,
    device_map=None,
    max_memory=None,
    no_split_module_classes=None,
    offload_folder=None,
    offload_buffers=None,
    offload_state_dict: bool = False,
)
```

Loads quantized weights into a converted model and dispatches them with Accelerate.

Operating notes:

- Requires `gptqmodel>=7.0.0` and `accelerate`.
- If `device_map` is `None`, Optimum uses the current CUDA device. In portable code, pass `device_map` explicitly, usually `"auto"` or a concrete device map.
- `backend` is converted to the GPT-QModel backend enum. Invalid backend names raise an error; retry with `"auto"`.
- Quantization config is read from `model.config.quantization_config` when present, otherwise from `save_folder/quant_config_name`.
- If config loading fails, Optimum raises a `ValueError` that points to the save folder and suggests ensuring `config.json` contains `quantization_config` for a Transformers-pretrained directory.
- If `no_split_module_classes` is absent, Optimum derives it from the class of the first block at `block_name_to_quantize`.
- The returned model is marked quantized, set to GPTQ quantization method, and switched to eval mode.

## Helper functions

### `get_seqlen(model)`

Reads `model.config.to_dict()` and returns the first available key among:

```text
max_position_embeddings, seq_length, n_positions
```

If none exist, logs a message and returns `2048`. Set `model_seqlen` manually when `2048` is wrong.

### `get_block_name_with_pattern(model)`

Searches model module names for these known block path prefixes:

```text
transformer.h
model.decoder.layers
gpt_neox.layers
model.layers
model.language_model.layers
h
decoder.layers
layers
```

Raises `ValueError` asking for `block_name_to_quantize` when no pattern matches.

### `get_preceding_modules(model, module_name)`

Returns module names encountered before the block module in the module tree. Use this to populate `module_name_preceding_first_block` for ordinary Transformers models, and verify manually for custom architectures.

### `get_layers(module, prefix=None)`

Internal utility used by conversion/packing. It finds exact `torch.nn.Linear` layers plus supported Conv1D/Conv2d layers, optionally restricted to a dotted prefix. For selective quantization, derive names from the actual block module rather than guessing.

## Dataset helpers

### `prepare_dataset(examples, batch_size=1, pad_token_id=None)`

Converts a list of examples with `input_ids` and `attention_mask` into batched `torch.LongTensor` dictionaries. Requires `pad_token_id` if `batch_size > 1`.

### `collate_data(blocks, contain_labels=False, pad_token_id=None)`

Pads and concatenates tokenized blocks into one batch. Labels are padded with `-100` when `contain_labels=True`.

### `get_dataset(dataset_name, tokenizer, nsamples=128, seqlen=2048, seed=0, split="train")`

Loads and tokenizes one of:

```text
wikitext2, c4, c4-new
```

`split` must be `"train"` or `"validation"`. `ptb` and `ptb-new` are deprecated and raise an error. This helper requires the `datasets` package and dataset access; avoid it for offline or no-download probes.
