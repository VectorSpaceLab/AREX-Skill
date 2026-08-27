# LoRA and Prompt Adapter Workflows

Use this reference for vLLM LoRA adapter setup, per-request adapter selection, server flags, dynamic resolver behavior, and compatibility checks. General generation parameters belong in the offline inference skill.

## Offline LoRA usage

A vLLM model can use LoRA only when the base model implements LoRA support and the engine is created with LoRA enabled.

```python
from vllm import LLM, SamplingParams
from vllm.lora.request import LoRARequest

llm = LLM(
    model="meta-llama/Llama-3.2-3B-Instruct",
    enable_lora=True,
    max_loras=2,
    max_lora_rank=64,
)

sampling = SamplingParams(temperature=0, max_tokens=128)
outputs = llm.generate(
    ["Write a SQL query for ..."],
    sampling,
    lora_request=LoRARequest("sql_adapter", 1, "/adapters/sql"),
)
text = outputs[0].outputs[0].text
```

`LoRARequest` fields:

- `lora_name`: human-readable adapter name. Match this with logs and server model IDs.
- `lora_int_id`: globally unique integer ID in the engine. Do not reuse the same integer for different adapter paths in one process.
- `lora_path`: local adapter directory or resolved local cache path containing adapter files.

For batched offline calls, a single `LoRARequest` applies to all inputs, or a sequence can apply per input in APIs that accept a list.

## Serving static LoRA modules

Start the server with LoRA enabled and declare adapters:

```bash
vllm serve meta-llama/Llama-3.2-3B-Instruct \
  --enable-lora \
  --max-loras 4 \
  --max-lora-rank 64 \
  --lora-modules sql-lora=/adapters/sql summarizer=/adapters/summarizer
```

Clients select the adapter by setting the OpenAI request `model` field to the adapter name:

```bash
curl http://localhost:8000/v1/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"sql-lora","prompt":"San Francisco is a","max_tokens":7,"temperature":0}'
```

`--lora-modules` supports both `name=path` and JSON entries with base model metadata:

```bash
--lora-modules '{"name":"sql-lora","path":"/adapters/sql","base_model_name":"meta-llama/Llama-3.2-3B-Instruct"}'
```

Use JSON form when the server's `/v1/models` response or downstream routing needs to expose the adapter's base model identity.

## Dynamic LoRA loading and resolvers

Dynamic adapter mutation is intentionally gated. Only enable it in trusted environments:

```bash
export VLLM_ALLOW_RUNTIME_LORA_UPDATING=True
```

Load/unload endpoints:

```bash
curl -X POST http://localhost:8000/v1/load_lora_adapter \
  -H 'Content-Type: application/json' \
  -d '{"lora_name":"sql_adapter","lora_path":"/adapters/sql"}'

curl -X POST http://localhost:8000/v1/unload_lora_adapter \
  -H 'Content-Type: application/json' \
  -d '{"lora_name":"sql_adapter"}'
```

For replacing weights under the same name, set `load_inplace: true` in the load request.

Resolver plugins can map an incoming adapter name to a local adapter path. Built-in resolver categories include a filesystem resolver and a Hugging Face Hub resolver. Remote resolvers and runtime mutation are not safe defaults for production because they may download and execute unreviewed adapter assets; use static `--lora-modules` when possible.

## Mixed MoE LoRA formats

Some MoE deployments need both 2D and 3D adapter layouts. Use server support for mixed MoE LoRA format only when the base model and adapters require it, and declare the adapter layout explicitly. Rank and tensor-parallel constraints become stricter for fully sharded or expert-parallel MoE adapters; incompatibilities usually surface as rank divisibility, target module, or tensor shape errors.

## Compatibility checklist

Before debugging generation quality, check configuration compatibility:

1. Base model supports LoRA (`SupportsLoRA`) and was initialized with `enable_lora=True` or `--enable-lora`.
2. Adapter files match the base model family, hidden size, tokenizer/vocab changes, and target modules.
3. `max_lora_rank` is at least the adapter rank.
4. `max_loras`, `max_cpu_loras`, and adapter cache sizes cover expected concurrency.
5. `lora_int_id` is unique per adapter in offline code.
6. The OpenAI `model` request exactly matches the server adapter name, not the local directory basename unless those are intentionally the same.
7. For MoE/fully sharded adapters, rank divisibility and 2D/3D layout are compatible with tensor/expert parallelism.
8. If an adapter adds vocabulary, confirm tokenizer and padding behavior are compatible with the base model and vLLM version.

## Prompt adapters

When a task mentions prompt adapters or adapter-style prompt conditioning, first confirm the current vLLM build exposes the needed prompt-adapter API/CLI flags. Treat prompt adapters as model- and version-dependent. Keep them separate from LoRA: LoRA changes model weights for selected modules; prompt adapters alter prompt-side conditioning and may have different initialization and serving flags.

## Troubleshooting signals

- `No free adapter slots`: increase `max_loras`/cache capacity or reduce concurrent distinct adapters.
- Adapter not used in server request: the request `model` does not match a loaded adapter name, or the server was not started with `--enable-lora`.
- Rank error: increase `max_lora_rank`, use an adapter with a lower rank, or fix tensor-parallel divisibility for sharded/MoE adapters.
- Target module error: adapter `target_modules` do not map to vLLM-supported wrapped modules for this base model.
- Dynamic load rejected: `VLLM_ALLOW_RUNTIME_LORA_UPDATING` is unset, the adapter path is inaccessible, or the resolver did not find valid adapter files.
- Quality regression with no runtime error: verify base model revision, tokenizer revision, adapter base model, chat template, and sampling params match the adapter's training setup.
