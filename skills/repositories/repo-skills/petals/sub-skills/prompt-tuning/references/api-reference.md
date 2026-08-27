# Prompt-Tuning API Reference

`PTuneConfig` adds `pre_seq_len: int = 0` and `tuning_mode: Optional[str] = None`. Supported tuning modes are `"ptune"` and `"deep_ptune"`. If tuning mode is set, `pre_seq_len` must be greater than zero.

`PTuneMixin` initializes prompt embeddings. In `deep_ptune`, it also initializes intermediate prompt embeddings that are reshaped to `[num_layers, batch, prefix_len, hidden]` before remote blocks use them.

Distributed model constructors accept prompt-tuning kwargs through `from_pretrained(...)`:

```python
AutoDistributedModelForCausalLM.from_pretrained(model_id, tuning_mode="ptune", pre_seq_len=16)
AutoDistributedModelForSequenceClassification.from_pretrained(model_id, num_labels=2, tuning_mode="deep_ptune", pre_seq_len=8)
```

Forward restrictions from the distributed model wrappers still apply: arbitrary custom attention masks, head masks, hidden-state output capture, and unsupported position patterns are not ordinary Petals paths.

PEFT utility behavior is safety-oriented: adapter loading checks for safetensors adapter weights and rejects repositories that do not expose the expected safe artifact. Server-side adapter preloading can depend on bitsandbytes and backend compatibility.
