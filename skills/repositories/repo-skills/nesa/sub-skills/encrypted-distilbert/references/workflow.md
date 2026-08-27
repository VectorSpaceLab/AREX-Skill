# Encrypted DistilBERT Workflow

This reference distills the minimal sentiment-classification demo into a
self-contained workflow.

## Inputs

- A short English text prompt.
- Either:
  - a local encrypted DistilBERT model directory with tokenizer files and model
    weights, or
  - a Hugging Face model id and permission to download/cache model files.
- Python with `torch`, `transformers`, and `safetensors` installed.

## Expected local model layout

A local model directory should contain at least:

- `config.json`
- `tokenizer_config.json`
- `special_tokens_map.json`
- one of `tokenizer.json`, `vocab.txt`, `tokenizer.model`, or an equivalent
  tokenizer artifact
- one of `model.safetensors`, `pytorch_model.bin`, or an equivalent model weight
  file

The model config should define an `id2label` mapping. For the sentiment demo,
expect two labels such as positive/negative or equivalent task-specific labels.
Always read the actual config instead of assuming label order.

## Local execution recipe

```bash
python scripts/validate_model_dir.py /path/to/encrypted-distilbert
python scripts/run_local_demo.py --model /path/to/encrypted-distilbert \
  --prompt "I feel safer using private AI"
```

The demo wrapper prints:

- the plaintext prompt length;
- encrypted token IDs visible to the simulated server;
- raw probabilities by label; and
- the top label.

## Hugging Face execution recipe

When the user authorizes network access, use a public model id:

```bash
python scripts/run_local_demo.py \
  --model nesaorg/distilbert-sentiment-encrypted \
  --prompt "I feel safer using private AI"
```

If the exact model id has changed, ask the user for the model id or search the
current project documentation. Do not silently substitute a generic DistilBERT
checkpoint; the point of this workflow is the encrypted tokenizer/model pair.

## How to explain results

Use this framing:

- The token IDs are the server-visible encrypted representation for the demo.
- The server-side model sees token IDs and returns logits/probabilities.
- The label mapping comes from the model config.
- The client is the only side that should know the plaintext prompt and tokenizer
  mapping.

Avoid overclaiming:

- A local demo does not prove all Nesa deployments are secure.
- Sentiment classification probabilities are model outputs, not decrypted text.
- The public community model card describes approximate fidelity, not a formal
  security theorem.

## Validation checklist

Before reporting success:

1. Model directory or model id is explicitly named.
2. `torch` and `transformers` import in the environment used for the run.
3. The tokenizer loads from the same source as the model.
4. The model output has a sequence-classification logits tensor.
5. The printed label names come from `config.id2label`.
6. Any network download/cache use is disclosed.
