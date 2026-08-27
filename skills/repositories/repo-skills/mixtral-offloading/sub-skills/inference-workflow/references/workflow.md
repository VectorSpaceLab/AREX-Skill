# Offloaded Mixtral inference workflow

This reference distills the repository's demo workflow into a scriptable plan.
It avoids depending on the original notebook and keeps network/model-download
steps explicit.

## Runtime assumptions

- The repository is source-only. Import its modules as `src.*` only after the
  user's checkout root is on `PYTHONPATH` or otherwise added to `sys.path`.
- Actual generation requires CUDA. CPU can validate config math and imports, but
  it cannot prove the Triton/HQQ offloaded inference path.
- Runtime dependencies are the repository runtime stack: PyTorch, Transformers
  4.36.1-era Mixtral classes, HQQ, Triton, safetensors, NumPy, and tqdm.
- The demo model target is `mistralai/Mixtral-8x7B-Instruct-v0.1`; the quantized
  state directory must match that architecture and include safetensors shards.

## State directory contract

`build_model(..., state_path=...)` expects a local directory with a
`model.safetensors.index.json` file. The code reads weight-map entries such as:

- `model.embed_tokens.weight` for the trunk shard.
- `model.layers.<layer>.block_sparse_moe.experts.<expert>.w1.W_q` for expert
  shard lookup.

Before running model construction, validate that:

1. `model.safetensors.index.json` exists and is valid JSON.
2. The JSON has a top-level `weight_map` object.
3. At least one trunk key and one expert quantized key are present.
4. Referenced safetensors shard files exist under the same state directory.

Do not let a future agent silently substitute the base unquantized Mixtral
checkpoint for this state directory; the offloading code expects HQQ-quantized
weights with the repo's state-dict structure.

## Scriptable setup outline

```python
import sys
from pathlib import Path

repo_root = Path('/path/to/user/mixtral-offloading')
sys.path.insert(0, str(repo_root))

import torch
from hqq.core.quantize import BaseQuantizeConfig
from transformers import AutoConfig, AutoTokenizer, TextStreamer

from src.build_model import OffloadConfig, QuantConfig, build_model

model_name = 'mistralai/Mixtral-8x7B-Instruct-v0.1'
quantized_state_path = Path('/path/to/Mixtral-8x7B-Instruct-v0.1-offloading-demo')
config = AutoConfig.from_pretrained(str(quantized_state_path))

device = torch.device('cuda:0')
offload_per_layer = 4
num_experts = config.num_local_experts

offload_config = OffloadConfig(
    main_size=config.num_hidden_layers * (num_experts - offload_per_layer),
    offload_size=config.num_hidden_layers * offload_per_layer,
    buffer_size=4,
    offload_per_layer=offload_per_layer,
)

attn_config = BaseQuantizeConfig(
    nbits=4,
    group_size=64,
    quant_zero=True,
    quant_scale=True,
)
attn_config['scale_quant_params']['group_size'] = 256

ffn_config = BaseQuantizeConfig(
    nbits=2,
    group_size=16,
    quant_zero=True,
    quant_scale=True,
)
quant_config = QuantConfig(ffn_config=ffn_config, attn_config=attn_config)

model = build_model(
    device=device,
    quant_config=quant_config,
    offload_config=offload_config,
    state_path=str(quantized_state_path),
)
```

Use the bundled `render_generation_skeleton.py` script to emit a fuller starter
file with validation comments and generation scaffolding.

## Generation loop pattern

The demo uses `AutoTokenizer`, `TextStreamer`, cached `past_key_values`, and
sampling parameters. Key details:

- Convert a single user message with `tokenizer.apply_chat_template`.
- Move input IDs to the CUDA device used by the model.
- For the first turn, `attention_mask = torch.ones_like(input_ids)`.
- For later turns, account for the cached sequence length using
  `past_key_values[0][0][0].size(1)` and build an attention mask on the same
  device.
- Call `model.generate(..., return_dict_in_generate=True,
  output_hidden_states=True)` and retain `result['past_key_values']`.

Keep `max_new_tokens`, `temperature`, and `top_p` configurable in a real script.
The notebook default uses `max_new_tokens=512`, `temperature=0.9`, and
`top_p=0.9`.

## Safe validation before an expensive run

1. Run the root environment helper with CUDA required.
2. Validate the state directory and index before loading weights.
3. Compute offload sizes with `create_offload_config.py`.
4. Run `python -m py_compile` on the generated script.
5. Start with a short prompt and a low `max_new_tokens` value before long chat.

## What not to automate without approval

- Downloading tens of gigabytes of model or tokenizer artifacts.
- Running an interactive infinite chat loop.
- Changing CUDA/PyTorch/HQQ versions in a shared environment.
- Treating CPU import success as proof of the offloaded CUDA generation path.
