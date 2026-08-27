# Inference workflows

## Pick the right entry point

| Need | Best entry point |
| --- | --- |
| Supported xTuring family | `BaseModel.create("<family-key>")` |
| Saved xTuring checkpoint | `BaseModel.load("./saved_dir")` for registry-backed families |
| Plain Hugging Face checkpoint for a supported family | `BaseModel.load("./hf_dir", model_name="<family-key>")` |
| Arbitrary checkpoint or local directory | `GenericModel("./checkpoint-or-repo-id")` or another `Generic*` class |
| Bundled `x/...` artifact | `BaseModel.load("x/...")` |

## Create or load

```python
from xturing.models import BaseModel, GenericModel

# Registry-backed family
model = BaseModel.create("qwen3_0_6b_lora")

# Saved xTuring checkpoint
restored = BaseModel.load("./saved_model")

# Plain local checkpoint for a supported family
local_hf = BaseModel.load("./hf_checkpoint", model_name="gpt2")

# Bundled hub checkpoint
hub_model = BaseModel.load("x/distilgpt2_lora_finetuned_alpaca")

# Arbitrary checkpoint or repo id
any_model = GenericModel("facebook/opt-1.3b")
```

## Tune generation before calling `generate`

`model.generation_config()` returns the mutable generation config that was merged from the package defaults and the model key.

```python
cfg = model.generation_config()
cfg.max_new_tokens = 128
cfg.do_sample = False
cfg.top_k = 4
cfg.top_p = 0.9
cfg.penalty_alpha = 0.6

output = model.generate(texts="Why are small language models useful?")
```

Notes:
- A scalar `texts` input returns a single string.
- A list of strings returns a list of strings.
- `dataset=...` generation uses the dataset collator and `batch_size`.

## Save and reopen

```python
from pathlib import Path

save_dir = Path("./saved_model")
model.save(str(save_dir))

# Registry-backed families
reloaded = BaseModel.load(str(save_dir))
```

What `save()` writes:
- model weights
- tokenizer files
- `xturing.json` metadata
- adapter files when the engine variant uses them

For generic checkpoints, save with the wrapper and reopen with the same wrapper or `BaseModel.load`:

```python
from xturing.models import GenericModel

generic = GenericModel("facebook/opt-1.3b")
generic.save("./generic_checkpoint")
reopened = GenericModel("./generic_checkpoint")
```

## Generic wrapper workflow

Use the generic wrappers when the architecture is not already covered by a family-specific key:

```python
from xturing.models import GenericModel, GenericLoraModel

model = GenericModel("facebook/opt-1.3b")
lora = GenericLoraModel("facebook/opt-1.3b", target_modules=["q_proj", "v_proj"])
```

Guidance:
- Use `c_attn` for GPT-2-like blocks.
- Use `q_proj` / `v_proj` for most decoder-only transformer families.
- If the target modules do not exist, the loader will raise a target-module error.
- If you have a local Hugging Face checkpoint directory without `xturing.json`, pass the family key through `BaseModel.load(path, model_name="<family-key>")` or use a `Generic*` wrapper directly.

## Generation defaults

Model construction loads defaults from `generation_config.yaml` using the model key.
Common patterns:
- smaller GPT-style models often use sampling defaults
- large models often use `max_new_tokens=512`
- some families prefer contrastive search settings

If the defaults are not right, mutate the config object before calling `generate`.

## Bundled hub paths

`BaseModel.load("x/...")` only works for the small fixed set of bundled paths in the hub helper.

| Hub path group | Typical use |
| --- | --- |
| `x/gpt2`, `x/gpt2_lora` | GPT-2 checkpoints |
| `x/distilgpt2`, `x/distilgpt2_lora` | DistilGPT-2 checkpoints |
| `x/distilgpt2_lora_finetuned_alpaca`, `x/llama_lora_finetuned_alpaca`, `x/llama_lora_int4` | bundled example checkpoints |
| `x/llama_lora` | bundled LLaMA LoRA checkpoint |

If the path is not in that list, treat it as a local path or a model hub ID, not a bundled xTuring artifact.

## Backend caveats

- Base INT8 variants use the CPU ITRex path when CUDA is absent.
- LoRA + INT8 and K-bit variants are CUDA-sensitive and depend on the quantization backend being available.
- K-bit variants are the least portable save/reopen path; verify the exact family before treating a saved directory as a durable checkpoint.
- `StableDiffusion` is not a usable inference target yet.
