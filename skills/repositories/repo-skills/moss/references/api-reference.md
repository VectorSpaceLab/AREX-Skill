# MOSS API reference

## Purpose

Read this for source-backed public API facts that are shared across MOSS
runtime, inference, serving, and fine-tuning workflows. See sub-skill references
for workflow-specific command templates and troubleshooting.

## Verified package/runtime facts

The repository is not a normal installable Python distribution. Public runtime
objects come from source modules or from Hugging Face remote-code checkpoint
loading.

Verified dependency versions during skill creation included PyTorch
`1.13.1+cu117`, Transformers `4.25.1`, Accelerate `1.0.1`, Hugging Face Hub
`0.36.2`, and Datasets `3.1.0`. Treat those as evidence for the generated
skill, not as the only supported versions.

## Model classes

| Object | Import surface | Verified role |
| --- | --- | --- |
| `MossConfig` | `models.configuration_moss` or remote code | `PretrainedConfig` subclass with `model_type="moss"`. |
| `MossTokenizer` | `models.tokenization_moss` or remote code | Byte-level BPE tokenizer with `vocab.json` and `merges.txt`. |
| `MossModel` | `models.modeling_moss` or remote code | Base transformer with cache/attention/hidden-state outputs. |
| `MossForCausalLM` | `models.modeling_moss` or remote code | Causal LM head and generation-compatible wrapper. |

`MossConfig()` verified defaults include vocabulary size `107008`, context
length `2048`, hidden size `4096`, layer count `28`, head count `16`, rotary
size `64`, `bos_token_id=106028`, `eos_token_id=106068`, `wbits=32`, and
`groupsize=128`.

## Inference wrapper facts

Source evidence exposed these signatures:

```python
Inference(model=None, model_dir=None, parallelism=True, device_map=None) -> None
Inference.forward(data: str, paras: Optional[Dict[str, float]] = None) -> List[str]
Inference.streaming_topk_search(
    input_ids,
    attention_mask,
    temperature=0.7,
    repetition_penalty=1.02,
    top_k=0,
    top_p=0.8,
    max_iterations=1024,
    regulation_start=512,
    length_penalty=1,
    max_time=60,
)
```

The default parameter dictionary used by that wrapper sets `temperature=0.7`,
`top_p=0.8`, `top_k=0`, `repetition_penalty=1.02`, `max_iterations=512`,
`regulation_start=512`, `length_penalty=1`, and `max_time=60`.

The bundled [../sub-skills/inference/scripts/run_moss_generation.py](../sub-skills/inference/scripts/run_moss_generation.py)
provides a self-contained template for future use and does not require the
original wrapper to remain available.

## Serving payload API

The FastAPI-style service route uses POST `/` with a JSON request containing:

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `prompt` | string | required | New user message. |
| `uid` | string or omitted | generated | Conversation id used to retain history. |
| `max_length` | integer | 2048 | Full sequence maximum passed to generation. |
| `top_p` | float | 0.8 | Nucleus sampling. |
| `temperature` | float | 0.7 | Sampling temperature. |

Response fields are `response`, `history`, `status`, `time`, and `uid`. Use
[../sub-skills/serving/scripts/moss_request_template.py](../sub-skills/serving/scripts/moss_request_template.py)
to produce validated payloads and
[../sub-skills/serving/scripts/serve_moss_api.py](../sub-skills/serving/scripts/serve_moss_api.py)
for a dry-run-first bundled service template.

## SFT dataset API facts

The training data loader signature is:

```python
SFTDataset(data_dir, tokenizer, data_type="train")
```

It expects `train.jsonl` or `val.jsonl` in the data directory unless cached
`<data_type>_data` and `<data_type>_no_loss_spans` tensors already exist. It
reads conversation records, tokenizes the meta instruction and turn strings,
masks the meta instruction plus inner tool-result payload spans with label
`-100`, skips samples with no useful turns, and does not include a turn that
would push the sequence above the 2048-token limit.

Use [../sub-skills/fine-tuning-data/scripts/validate_sft_json.py](../sub-skills/fine-tuning-data/scripts/validate_sft_json.py)
for safe schema validation before tokenizer or model work.
