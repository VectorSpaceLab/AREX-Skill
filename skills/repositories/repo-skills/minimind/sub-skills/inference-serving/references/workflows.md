# MiniMind inference-serving workflows

This reference turns the MiniMind inference evidence into self-contained operating workflows. Use placeholders such as `MODEL_DIR`, `WEIGHTS_DIR`, and `TOKENIZER_DIR`; do not assume a source checkout exists.

## 1. Decide the serving format

| Input artifact | Best use | Required evidence | First action |
| --- | --- | --- | --- |
| Transformers-format directory | Local chat, OpenAI-compatible server, WebUI, vLLM/SGLang, conversion to GGUF/Ollama | `config.json`, tokenizer files, model weight file(s), chat template | `python scripts/check_model_artifacts.py --model-dir MODEL_DIR --expect transformers --check-imports` |
| Raw MiniMind `.pth` checkpoint | Educational/local PyTorch inference with MiniMind modules present | `WEIGHTS_DIR/<weight>_<hidden_size>[_moe].pth`, tokenizer directory, matching config dimensions | `python scripts/check_model_artifacts.py --weights-dir WEIGHTS_DIR --tokenizer-dir TOKENIZER_DIR --expect raw-torch --weight full_sft --hidden-size 768` |
| Raw base `.pth` + LoRA `.pth` | Local raw inference, then merge/export if serving elsewhere | base checkpoint and LoRA checkpoint with the same hidden size/MoE choice | Validate both files, merge LoRA to a full raw checkpoint, then convert/export |
| GGUF/Ollama package | Lightweight local runtime after conversion | GGUF file and a MiniMind-compatible prompt template | Validate template stop tokens and tool/thinking tags before API routing |

Prefer Transformers-format directories for anything that must survive outside a MiniMind Python environment.

## 2. Local non-serving inference

### Transformers-format directory

Use this path when `MODEL_DIR` has model weights and tokenizer files. The key behavior is that MiniMind relies on the tokenizer chat template for roles, `<think>`, tool schemas, and tool-response turns.

```bash
python - <<'PY'
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_DIR = "MODEL_DIR"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
OPEN_THINKING = False

messages = [{"role": "user", "content": "Introduce MiniMind in one sentence."}]
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(MODEL_DIR, trust_remote_code=True).eval().to(DEVICE)

prompt = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True,
    open_thinking=OPEN_THINKING,
)
inputs = tokenizer(prompt, return_tensors="pt", truncation=True).to(DEVICE)
with torch.no_grad():
    output_ids = model.generate(
        inputs["input_ids"],
        attention_mask=inputs.get("attention_mask"),
        max_new_tokens=256,
        do_sample=True,
        temperature=0.8,
        top_p=0.9,
        pad_token_id=tokenizer.pad_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )
print(tokenizer.decode(output_ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True))
PY
```

If CPU inference fails with half-precision operations, load the model without forcing `.half()` or use `torch_dtype=torch.float32`.

### Raw MiniMind PyTorch checkpoint

Raw `.pth` checkpoints are not self-contained. They need the MiniMind model implementation in the runtime environment and must match the checkpoint dimensions.

Expected dense checkpoint name:

```text
WEIGHTS_DIR/full_sft_768.pth
```

Expected MoE checkpoint name:

```text
WEIGHTS_DIR/full_sft_768_moe.pth
```

Generic raw-loading recipe:

```bash
python - <<'PY'
from transformers import AutoTokenizer
import torch
from model.model_minimind import MiniMindConfig, MiniMindForCausalLM

TOKENIZER_DIR = "TOKENIZER_DIR"
WEIGHT_PATH = "WEIGHTS_DIR/full_sft_768.pth"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_DIR)
config = MiniMindConfig(hidden_size=768, num_hidden_layers=8, use_moe=False)
model = MiniMindForCausalLM(config)
model.load_state_dict(torch.load(WEIGHT_PATH, map_location=DEVICE), strict=True)
model = model.eval().to(DEVICE)
if DEVICE == "cuda":
    model = model.half()

messages = [{"role": "user", "content": "What can MiniMind do?"}]
prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, open_thinking=False)
inputs = tokenizer(prompt, return_tensors="pt", truncation=True).to(DEVICE)
with torch.no_grad():
    generated = model.generate(inputs=inputs["input_ids"], attention_mask=inputs["attention_mask"], max_new_tokens=128)
print(tokenizer.decode(generated[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True))
PY
```

Use raw inference only when the MiniMind modules are intentionally present. For portable serving, convert raw weights to a Transformers directory first.

## 3. LoRA inference and export decision

| Goal | Decision |
| --- | --- |
| Quick local experiment with raw base model | Apply LoRA at load time, using the same base weight stage and hidden size used during LoRA training. |
| Long-running API server from raw MiniMind modules | Either stack LoRA at server startup or merge it first. Merge first if reproducibility matters. |
| Transformers/vLLM/llama.cpp/Ollama serving | Merge LoRA into a full raw checkpoint, then export the merged checkpoint to a Transformers/Qwen3-compatible directory. |
| Continued LoRA training or dataset design | Route out to `training-basics`; this sub-skill only covers inference/merge/export decisions. |

Check both candidate LoRA layouts because MiniMind evidence used both styles in different inference paths:

```text
WEIGHTS_DIR/lora_identity_768.pth
WEIGHTS_DIR/lora/lora_identity_768.pth
```

## 4. OpenAI-compatible serving workflow

1. Ensure dependencies are installed in the runtime environment: `fastapi`, `uvicorn`, `pydantic`, `torch`, `transformers`, and optionally `openai` for client probes. FastAPI/Uvicorn were required by the server evidence but were not listed in the runtime requirements evidence.
2. Prefer a Transformers-format model directory. Raw serving requires MiniMind modules and exact checkpoint dimensions.
3. Start a local server bound to a safe interface. The evidence server used `/v1/chat/completions` and port `8998`.
4. Probe with the bundled one-shot client:

```bash
python scripts/openai_chat_once.py \
  --base-url http://127.0.0.1:8998/v1 \
  --model minimind \
  --prompt "Who are you?" \
  --max-tokens 128 \
  --no-stream
```

5. For thinking output:

```bash
python scripts/openai_chat_once.py \
  --base-url http://127.0.0.1:8998/v1 \
  --model minimind \
  --prompt "Explain why the sky is blue." \
  --open-thinking \
  --stream
```

6. For tool schemas, pass a JSON file with OpenAI-compatible `tools` entries:

```bash
python scripts/openai_chat_once.py \
  --base-url http://127.0.0.1:8998/v1 \
  --model minimind \
  --prompt "Calculate 256 * 37." \
  --tools-json tools.json \
  --no-stream
```

See [api-and-serving.md](api-and-serving.md) for exact request/response fields.

## 5. Tool-call loop workflow

MiniMind uses text tags in its chat template:

```text
<tool_call>{"name": "calculate_math", "arguments": {"expression": "256 * 37"}}</tool_call>
<tool_response>{"result": "9472"}</tool_response>
```

Use this self-contained smoke before debugging a live model:

```bash
python scripts/toolcall_smoke.py --execute --json
```

Operational loop:

1. Send user message and optional `tools` schema to the tokenizer/API.
2. Parse assistant content for `<tool_call>...</tool_call>` JSON objects or OpenAI `message.tool_calls`.
3. Execute only allowed local tools; never evaluate untrusted expressions directly.
4. Append a tool-role message containing JSON observation.
5. Ask the model again until no tool calls remain or a strict turn cap is reached.

The WebUI evidence capped repeated tool-call continuations at 16 loops. Use a lower cap for automation unless the task explicitly needs multi-step tool use.

## 6. Adaptive thinking workflow

`open_thinking` is a generation-template switch, not a separate model class.

- `open_thinking=false`: the template injects an empty `<think>\n\n</think>` block before the answer, nudging direct answers.
- `open_thinking=true`: the template injects `<think>\n` and lets the model continue with explicit reasoning text before `</think>` and final answer.
- OpenAI-compatible requests may carry this as top-level `open_thinking` or under `chat_template_kwargs.open_thinking` / `chat_template_kwargs.enable_thinking`.
- The API parser moves extracted thinking text into `reasoning_content`.

Known limitation: explicit thinking and tool calling together were documented as unstable because joint reasoning+tool-call data was limited. If a task requires reliable tool use, consider keeping explicit thinking off for tool turns.

## 7. Streamlit WebUI workflow constraints

The WebUI evidence is interactive and should be treated as reference-only. If recreating a WebUI around MiniMind:

- Use Transformers-format model directories; the UI evidence scanned child directories for `.bin`, `.safetensors`, `.pt`, or `model.safetensors.index.json` files.
- Install `streamlit` separately if absent.
- Keep the model directory explicit rather than relying on a script-directory scan.
- Tool selection was capped at four enabled tools.
- The UI displayed `<think>` content in collapsible blocks and formatted `<tool_call>` / tool-result blocks.
- Thinking may be unstable with multi-turn history or active tools.

## 8. Conversion and third-party serving workflow

1. Validate raw or Transformers artifacts with `scripts/check_model_artifacts.py`.
2. If starting from raw `.pth`, export to Qwen3-compatible Transformers format for broad engine compatibility when possible.
3. Confirm the runtime `transformers` package exposes `Qwen3Config`, `Qwen3ForCausalLM`, `Qwen3MoeConfig`, and `Qwen3MoeForCausalLM` before Qwen3-compatible export. Inspection evidence showed these classes are available in Transformers `4.57.6`.
4. For vLLM/SGLang, use the Qwen3-compatible Transformers directory and validate `/v1/chat/completions` behavior with `scripts/openai_chat_once.py`.
5. For llama.cpp, convert the Transformers directory to GGUF, then optionally quantize.
6. For Ollama, create an Ollama model from the GGUF file with a template preserving `<|im_start|>`, `<|im_end|>`, `<think>`, `<tool_call>`, and `<tool_response>` semantics.

Concrete templates and caveats are in [cli-reference.md](cli-reference.md).
