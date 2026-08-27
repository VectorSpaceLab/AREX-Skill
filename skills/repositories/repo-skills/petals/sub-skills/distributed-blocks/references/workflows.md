# Distributed Block Workflows

## Slice remote blocks

```python
from petals import AutoDistributedConfig, RemoteSequential
config = AutoDistributedConfig.from_pretrained("MODEL_ID", initial_peers=initial_peers)
blocks = RemoteSequential(config, start_block=3, end_block=6)
hidden = torch.randn(batch, seq, config.hidden_size)
out = blocks(hidden)
```

Use slices for advanced routing or exactness checks, not for ordinary token generation.

## Local block inspection

Use `load_pretrained_block` only after the user approves any model artifact downloads/cache use. It loads one block, not the whole distributed model.

## Tensor parallel and quantization planning

Tensor parallel is most reliable for BLOOM in this snapshot. For non-BLOOM multi-device conversion, preserve a caution. Quantization names `int8` and `nf4` require a working bitsandbytes stack; use `none` when unverified.

## DHT prefix and block ranges

Servers announce keys from the distributed config's `dht_prefix` and block indices. A client with the wrong prefix or missing block range will route forever or fail with missing-block errors.

## Speculative Llama internals

Speculative generation validates tokens from a local small model with the distributed Llama model. In this snapshot it is constrained to non-sampling paths and depends on active session budget.
