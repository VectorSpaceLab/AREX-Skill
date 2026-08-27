# CLI and artifact reference

This reference gives concrete command surfaces without requiring agents to reopen MiniMind source files. Use the bundled scripts for validation and API probes; use the command templates as self-contained recipes.

## Artifact checker

Run from the sub-skill directory or adjust paths to the bundled scripts.

### Transformers directory

```bash
python scripts/check_model_artifacts.py \
  --model-dir MODEL_DIR \
  --expect transformers \
  --check-imports \
  --json
```

Expected artifacts:

| File | Required? | Purpose |
| --- | --- | --- |
| `config.json` | yes | Model type, dimensions, MoE/Qwen3/MiniMind metadata, optional RoPE scaling. |
| `tokenizer.json` | yes in normal releases | Tokenizer vocabulary. |
| `tokenizer_config.json` | yes for chat behavior | Chat template; should contain `<think>`, `<tool_call>`, and `<tool_response>` when thinking/tools are needed. |
| `special_tokens_map.json` | recommended | Confirms BOS/EOS/PAD mapping. |
| `generation_config.json` | optional | Default generation settings. |
| `model.safetensors`, `pytorch_model.bin`, or index files | yes | Model weights. |
| `model_minimind.py` or `auto_map` entries | only for MiniMind custom format | Requires `trust_remote_code=True`; Qwen3-compatible export should not rely on custom MiniMind code. |

### Raw torch checkpoint

```bash
python scripts/check_model_artifacts.py \
  --weights-dir WEIGHTS_DIR \
  --tokenizer-dir TOKENIZER_DIR \
  --expect raw-torch \
  --weight full_sft \
  --hidden-size 768 \
  --json
```

Raw checkpoint naming:

| Model type | Pattern | Example |
| --- | --- | --- |
| Dense base/stage | `<weight>_<hidden_size>.pth` | `full_sft_768.pth` |
| MoE base/stage | `<weight>_<hidden_size>_moe.pth` | `full_sft_768_moe.pth` |
| LoRA dense | `<lora_weight>_<hidden_size>.pth` or `lora/<lora_weight>_<hidden_size>.pth` | `lora_identity_768.pth` |
| LoRA MoE | `<lora_weight>_<hidden_size>_moe.pth` or `lora/<lora_weight>_<hidden_size>_moe.pth` | `lora_identity_768_moe.pth` |

Common weight prefixes seen in MiniMind evidence: `pretrain`, `full_sft`, `dpo`, `ppo_actor`, `grpo`, `agent`, plus custom LoRA names such as `lora_identity` or `lora_medical`.

## Distilled local inference parameters

MiniMind inference evidence used the following parameters. If writing a wrapper, prefer an explicit `--artifact-type` over substring-based path detection.

| Parameter | Meaning | Default evidence | Notes |
| --- | --- | --- | --- |
| `--load-from` / `MODEL_DIR` | Transformers directory or tokenizer/model module directory | `model` for raw, model directory for Transformers | A path containing the string `model` was treated as raw in evidence; avoid this ambiguity in new wrappers. |
| `--weights-dir` | Raw `.pth` directory | `out` | Needed only for raw MiniMind checkpoints. |
| `--weight` | Raw checkpoint prefix | `full_sft` | Must match available file and base used for LoRA. |
| `--lora-weight` | Optional LoRA prefix | `None` | Use only with raw MiniMind modules; merge before portable export. |
| `--hidden-size` | Model width | `768` | Must match checkpoint filename and config. |
| `--num-hidden-layers` | Number of layers | `8` | Must match checkpoint state dict. |
| `--use-moe` | Dense vs MoE | `0` | Adds `_moe` suffix to raw checkpoint names. |
| `--max-seq-len` | Raw model context allocation | `8192` in server path | Transformers config may expose larger tokenizer max length; generation still depends on memory and training length. |
| `--inference-rope-scaling` | Enable YaRN-style RoPE scaling in raw config | off | For Transformers, edit `config.json` `rope_scaling` instead. |
| `--max-new-tokens` / `max_tokens` | Generation budget | 512 to 8192 in evidence | Do not confuse with true long-context capability. |
| `--temperature` | Sampling temperature | 0.7-0.9 | Lower for deterministic probes. |
| `--top-p` | Nucleus sampling | 0.85-0.95 | Pair with temperature. |
| `--open-thinking` | Template-level explicit thinking switch | off | Available in CLI, API, and UI pathways. |
| `--history-turns` | Number of previous messages retained | 0 default in CLI evidence | Keep even user/assistant pairs when using history. |
| `--device` | `cuda`, `cpu`, or accelerator | auto CUDA if available | CPU half precision can fail; avoid forcing `.half()` on CPU. |

## Self-contained Transformers inference command

```bash
MODEL_DIR=MODEL_DIR python - <<'PY'
import os, torch
from transformers import AutoTokenizer, AutoModelForCausalLM
model_dir = os.environ["MODEL_DIR"]
device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_dir, trust_remote_code=True).eval().to(device)
messages = [{"role": "user", "content": "请用一句话介绍 MiniMind。"}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, open_thinking=False)
inputs = tokenizer(prompt, return_tensors="pt", truncation=True).to(device)
with torch.no_grad():
    out = model.generate(inputs["input_ids"], attention_mask=inputs.get("attention_mask"), max_new_tokens=128, temperature=0.8, top_p=0.9, do_sample=True, pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id)
print(tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True))
PY
```

Thinking-enabled variation:

```python
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, open_thinking=True)
```

Tool-enabled variation:

```python
tools = [{
    "type": "function",
    "function": {
        "name": "calculate_math",
        "description": "Calculate a simple arithmetic expression.",
        "parameters": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
    },
}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, tools=tools, open_thinking=False)
```

## Raw PyTorch inference command template

Raw checkpoint inference requires importable MiniMind modules. This is suitable for controlled environments, not portable model distribution.

```bash
TOKENIZER_DIR=TOKENIZER_DIR WEIGHT_PATH=WEIGHTS_DIR/full_sft_768.pth python - <<'PY'
import os, torch
from transformers import AutoTokenizer
from model.model_minimind import MiniMindConfig, MiniMindForCausalLM

tokenizer_dir = os.environ["TOKENIZER_DIR"]
weight_path = os.environ["WEIGHT_PATH"]
device = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
config = MiniMindConfig(hidden_size=768, num_hidden_layers=8, use_moe=False, inference_rope_scaling=False)
model = MiniMindForCausalLM(config)
model.load_state_dict(torch.load(weight_path, map_location=device), strict=True)
model = model.eval().to(device)
if device == "cuda":
    model = model.half()

messages = [{"role": "user", "content": "为什么天空是蓝色的？"}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, open_thinking=False)
inputs = tokenizer(prompt, return_tensors="pt", truncation=True).to(device)
with torch.no_grad():
    out = model.generate(inputs=inputs["input_ids"], attention_mask=inputs["attention_mask"], max_new_tokens=128, temperature=0.85, top_p=0.95)
print(tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True))
PY
```

LoRA-at-load-time raw variation:

```python
from model.model_lora import apply_lora, load_lora
apply_lora(model)
load_lora(model, "WEIGHTS_DIR/lora_identity_768.pth")
```

If the target is serving or conversion, merge LoRA first instead of relying on runtime stacking.

## RoPE scaling

Raw MiniMind config has an `inference_rope_scaling` switch that activates a YaRN-style `rope_scaling` config internally. Transformers-format models should carry the equivalent in `config.json`:

```json
"rope_scaling": {
  "type": "yarn",
  "factor": 16.0,
  "original_max_position_embeddings": 2048,
  "beta_fast": 32.0,
  "beta_slow": 1.0,
  "attention_factor": 1.0
}
```

RoPE extrapolation helps position encoding beyond training length; it does not guarantee factual long-context reasoning or fit memory budgets.

## Conversion/export plan templates

Use the artifact checker before conversion:

```bash
python scripts/check_model_artifacts.py \
  --weights-dir WEIGHTS_DIR \
  --tokenizer-dir TOKENIZER_DIR \
  --weight full_sft \
  --hidden-size 768 \
  --print-conversion-plan
```

### Raw torch to Qwen3-compatible Transformers

Best target for third-party engines.

Required runtime imports:

```python
from transformers import AutoTokenizer, Qwen3Config, Qwen3ForCausalLM, Qwen3MoeConfig, Qwen3MoeForCausalLM
from model.model_minimind import MiniMindConfig
```

Conversion outline:

1. Create `MiniMindConfig(hidden_size=..., num_hidden_layers=..., use_moe=...)` matching the checkpoint.
2. Load the raw `state_dict` from `<weight>_<hidden_size>[_moe].pth`.
3. Construct `Qwen3ForCausalLM` for dense or `Qwen3MoeForCausalLM` for MoE using matching dimensions.
4. For MoE exports, account for Qwen3MoE expert tensor layout differences in the installed Transformers version.
5. Load the remapped state dict strictly.
6. Save the model and tokenizer to `EXPORT_DIR`.
7. Re-run `scripts/check_model_artifacts.py --model-dir EXPORT_DIR --expect qwen3-transformers --check-imports`.

### Raw torch to MiniMind Transformers

Best target when preserving MiniMind custom model identity is more important than third-party engine compatibility.

Required behavior:

1. Register `MiniMindConfig` and `MiniMindForCausalLM` for auto classes.
2. Load the raw checkpoint into `MiniMindForCausalLM`.
3. Save model and tokenizer to `EXPORT_DIR`.
4. Consumers will generally need `trust_remote_code=True` unless the MiniMind classes are installed.

### Transformers to raw torch

Use only if a downstream raw MiniMind workflow specifically needs `.pth`:

```python
from transformers import AutoModelForCausalLM
import torch
model = AutoModelForCausalLM.from_pretrained("MODEL_DIR", trust_remote_code=True)
torch.save({k: v.cpu().half() for k, v in model.state_dict().items()}, "WEIGHTS_DIR/full_sft_768.pth")
```

### Merge raw base + LoRA

Use before portable export:

```python
from model.model_minimind import MiniMindConfig, MiniMindForCausalLM
from model.model_lora import apply_lora, merge_lora
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
config = MiniMindConfig(hidden_size=768, num_hidden_layers=8, use_moe=False)
model = MiniMindForCausalLM(config).to(device)
model.load_state_dict(torch.load("WEIGHTS_DIR/full_sft_768.pth", map_location=device), strict=False)
apply_lora(model)
merge_lora(model, "WEIGHTS_DIR/lora_identity_768.pth", "WEIGHTS_DIR/merged_identity_768.pth")
```

Then export `merged_identity_768.pth` to Transformers format.

## Third-party serving templates

### vLLM

Use a Qwen3-compatible Transformers directory when possible.

```bash
vllm serve MODEL_DIR \
  --model-impl transformers \
  --served-model-name minimind \
  --port 8998
```

Expect CUDA requirements and engine-specific memory limits. Probe with `scripts/openai_chat_once.py`.

### SGLang

```bash
python -m sglang.launch_server \
  --model-path MODEL_DIR \
  --attention-backend triton \
  --host 127.0.0.1 \
  --port 8998
```

Use only when CUDA/Triton dependencies are intentionally installed.

### llama.cpp

1. Start from a Transformers-format model directory.
2. If the converter does not recognize the tokenizer, configure a compatible tokenizer fallback such as `qwen2` in the converter.
3. Convert to GGUF:

```bash
python convert_hf_to_gguf.py MODEL_DIR
```

4. Optional quantization:

```bash
llama-quantize MODEL_DIR/model.gguf MODEL_DIR/model.q8.gguf Q8_0
```

5. CLI smoke:

```bash
llama-cli -m MODEL_DIR/model.gguf
```

### Ollama

Create a Modelfile around a GGUF export. Preserve MiniMind chat markers:

```text
FROM MODEL_DIR/model.gguf
SYSTEM "Your name is MiniMind. Answer helpfully and completely."
PARAMETER repeat_penalty 1
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"
PARAMETER temperature 0.9
PARAMETER top_p 0.9
PARAMETER num_ctx 8192
```

The full template should include `<think>`, `<tool_call>`, and `<tool_response>` blocks if tool/thinking behavior is required. After creation:

```bash
ollama create -f minimind.modelfile minimind-local
ollama run minimind-local
```

Validate tool calls explicitly; many third-party runtimes preserve the text tags but do not return OpenAI `tool_calls` objects unless wrapped by a parser.
