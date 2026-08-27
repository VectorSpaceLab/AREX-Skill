# Client Workflows

## Minimal generation against the public swarm

```python
from transformers import AutoTokenizer
from petals import AutoDistributedModelForCausalLM

model_name = "MODEL_ID_HOSTED_BY_PETALS"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoDistributedModelForCausalLM.from_pretrained(model_name)
input_ids = tokenizer("A cat sat", return_tensors="pt")["input_ids"]
output_ids = model.generate(input_ids, max_new_tokens=5, do_sample=False)
print(tokenizer.decode(output_ids[0], skip_special_tokens=True))
```

This proves client code shape only after the model/tokenizer and remote peers are reachable. For gated models, authenticate before loading tokenizer/config.

## Private swarm selection

```python
from petals import AutoDistributedModelForCausalLM
model = AutoDistributedModelForCausalLM.from_pretrained(
    "MODEL_ID",
    initial_peers=["/ip4/127.0.0.1/tcp/31337/p2p/PEER_ID"],
    dht_prefix="MODEL_DHT_PREFIX_IF_CUSTOM",
)
```

Every server and client in a private swarm must agree on model identifier, `dht_prefix`, bootstrap peers, and block ranges.

## Interactive generation with cache reuse

```python
with model.inference_session(max_length=prompt_tokens + 128) as session:
    out = model.generate(input_ids, max_new_tokens=1, do_sample=True, session=session)
    while need_more:
        out = model.generate(None, max_new_tokens=1, do_sample=True, session=session)
```

Reserve enough `max_length` for prompt plus all generated tokens. Avoid beam search in resumed sessions unless you have checked the warning for the target model.

## Sequence classification client

```python
from petals import AutoDistributedModelForSequenceClassification
model = AutoDistributedModelForSequenceClassification.from_pretrained(
    "MODEL_ID", num_labels=2, initial_peers=initial_peers
)
outputs = model(input_ids=input_ids, labels=labels)
```

Use this for inference or prompt-tuning heads; route training details to `prompt-tuning`.

## Speculative Llama generation

Speculative generation requires a supported distributed Llama model and a local `small_model` that proposes tokens. Use it only for greedy-style validation paths in this snapshot; sampling and synchronized GPU generation are explicitly constrained in the implementation.
