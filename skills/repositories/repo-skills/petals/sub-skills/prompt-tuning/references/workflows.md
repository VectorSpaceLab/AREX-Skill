# Prompt-Tuning Workflows

## Causal LM/chat prompt tuning

Use `AutoDistributedModelForCausalLM.from_pretrained(model_id, tuning_mode="ptune", pre_seq_len=N)` for a single learned prefix or `tuning_mode="deep_ptune"` for per-block prefixes. Tokenize text to fixed-length `input_ids`; use labels equal to token IDs with pad tokens masked to `-100`. Remove unsupported zero-valued attention masks before Petals model calls.

Training outline:

```python
model = AutoDistributedModelForCausalLM.from_pretrained(model_id, tuning_mode="ptune", pre_seq_len=16).to(device)
trainables = [p for p in model.parameters() if p.requires_grad]
optimizer = torch.optim.AdamW(trainables, lr=1e-2)
for batch in loader:
    batch.pop("attention_mask", None)
    batch = {k: v.to(device) for k, v in batch.items()}
    loss = model(**batch).loss
    loss.backward(); optimizer.step(); optimizer.zero_grad(set_to_none=True)
```

After tuning, keep using the same model object to generate with learned prompts. For interactive chat, create an `inference_session(max_length=...)` large enough for prompt plus generated answer.

## Sequence classification prompt tuning

Use `AutoDistributedModelForSequenceClassification.from_pretrained(model_id, num_labels=N, tuning_mode="ptune", pre_seq_len=N_PREFIX)`. Tokenize the text column, rename labels to `labels`, omit unsupported masks, and set tokenizer/model pad behavior intentionally for batched inputs.

The optimizer should update prompt embeddings and the classifier head only. Verify this before training.

## Adapter-aware prompt tuning

Server-side adapters are preloaded on Petals servers and selected by client config such as `active_adapter`. Prompt tuning trains local prompt/head parameters; it does not update adapter weights. Adapter repositories should be safetensors-based and available to servers.

## Use the skeleton generator

```bash
python scripts/prompt_tuning_skeleton.py --task classification --model MODEL_ID --num-labels 2 --pre-seq-len 16 --no-wandb
```

The script prints a plan and illustrative code only. It does not import Petals, download data, start a swarm, or train.
