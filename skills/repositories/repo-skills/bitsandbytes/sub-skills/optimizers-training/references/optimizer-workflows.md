# Optimizer Workflows

## Purpose

Use this reference to write practical PyTorch training loops with bitsandbytes optimizers and to decide when 8-bit, 32-bit, paged, `StableEmbedding`, and per-parameter overrides are appropriate.

## Drop-In Replacement

A bitsandbytes optimizer is usually constructed at the same point as a PyTorch optimizer:

```python
import bitsandbytes as bnb

optimizer = bnb.optim.AdamW8bit(model.parameters(), lr=2e-4, weight_decay=0.01)
```

Keep the rest of the training loop conventional:

```python
loss.backward()
optimizer.step()
optimizer.zero_grad(set_to_none=True)
```

Decision guide:

- Use `Adam8bit` or `AdamW8bit` when optimizer state memory is the bottleneck.
- Use `Adam32bit`, `AdamW32bit`, or generic `Adam(..., optim_bits=32)` when stability matters more than memory.
- Use `Lion8bit` only when the training recipe already calls for Lion-style updates.
- Use AdEMAMix variants only when the recipe expects `betas=(beta1, beta2, beta3)`, `alpha`, and optional schedule controls.

## `min_8bit_size` and Missing Memory Savings

The default `min_8bit_size=4096` keeps small parameter tensors in 32-bit even when the optimizer is an 8-bit class. This is intentional: biases, layer norm weights, and other small tensors save little memory and are often stability-sensitive.

Use a higher threshold when the user wants to preserve even more parameters in 32-bit:

```python
optimizer = bnb.optim.AdamW8bit(model.parameters(), lr=2e-4, min_8bit_size=16384)
```

Use a lower threshold only for controlled experiments or diagnostics:

```python
optimizer = bnb.optim.Adam8bit(model.parameters(), lr=1e-3, min_8bit_size=1)
```

If there are no visible savings, check whether most trainable tensors are below the threshold or whether activation memory, gradients, dataloader buffers, or model weights dominate the memory profile.

## Stable Embedding Pattern

For NLP models with learned token embeddings, replace standard embeddings with `StableEmbedding` when training with 8-bit optimizer states:

```python
import bitsandbytes as bnb

self.token_embedding = bnb.nn.StableEmbedding(num_embeddings=vocab_size, embedding_dim=hidden_size)
```

`StableEmbedding` is designed for improved training stability and 32-bit optimizer states for that layer. Keep it in the optimizer parameter list with the rest of the model; use `GlobalOptimManager` overrides if a custom module still needs explicit 32-bit treatment.

## Correct `GlobalOptimManager` Override Order

Use this order when a user asks for 8-bit Adam except embeddings, layer norm, or other unstable parameters in 32-bit:

```python
import bitsandbytes as bnb

manager = bnb.optim.GlobalOptimManager.get_instance()
model = MyModel()
manager.register_parameters(model.parameters())  # register while parameters are still on CPU

model = model.cuda()
optimizer = bnb.optim.Adam8bit(model.parameters(), lr=2e-4)

manager.override_config(model.embedding.weight, "optim_bits", 32)
manager.override_config(model.layer_norm.weight, "optim_bits", 32)
manager.override_config(model.layer_norm.bias, "optim_bits", 32)
```

Why the order matters:

- The manager records parameter identities/configs before optimizer state is initialized.
- Registering while parameters are still on CPU is the documented pattern.
- Overrides must target the exact `torch.nn.Parameter` object that the optimizer sees.
- If a module replaces a parameter after registration, re-register or override the new parameter object.

For multiple parameters, pass a list and a config dictionary:

```python
manager.override_config(
    [model.embedding.weight, model.layer_norm.weight, model.layer_norm.bias],
    key_value_dict={"optim_bits": 32},
)
```

For module-local overrides created inside a module constructor, use `register_module_override(module, param_name, config)` and keep the `param_name` aligned with the module attribute name.

## Paged Optimizers

Paged optimizers allocate optimizer state through unified-memory style paging for supported accelerator workflows. They are useful when optimizer state causes out-of-memory pressure, but paging becomes active only when memory pressure requires eviction and can add transfer overhead.

Typical choices:

```python
optimizer = bnb.optim.PagedAdamW8bit(model.parameters(), lr=2e-4)
optimizer = bnb.optim.PagedAdamW(model.parameters(), lr=2e-4, optim_bits=32)
optimizer = bnb.optim.PagedLion8bit(model.parameters(), lr=1e-4)
```

Notes distilled from the XPU and benchmark examples:

- Treat paged CPU/XPU/CUDA examples as hardware-specific reference patterns, not safe default smoke tests.
- Paged memory benchmarks need accelerator availability, model allocation, synchronization, and memory-stat APIs; do not run them as routine validation.
- Paged optimizers reduce peak accelerator state memory most when optimizer states are large enough to matter.
- If all state fits on device, paged optimizers may show little difference; if memory is evicted, step time can include CPU/device transfer overhead.

## State and Checkpoint Validation

Use normal PyTorch optimizer checkpoint APIs:

```python
payload = {"model": model.state_dict(), "optimizer": optimizer.state_dict()}
torch.save(payload, checkpoint_path)

payload = torch.load(checkpoint_path, map_location=device)
model.load_state_dict(payload["model"])
optimizer.load_state_dict(payload["optimizer"])
```

After loading, validate with a tiny batch:

1. Move the model and batch to the intended device.
2. Run forward, backward, `optimizer.step()`, and `optimizer.zero_grad()`.
3. Inspect `optimizer.state` for expected parameter keys and tensor devices.
4. If using 8-bit states, remember that small tensors below `min_8bit_size` can remain 32-bit by design.

## Bundled CPU Smoke

The bundled `scripts/cpu-optimizer-smoke.py` is adapted from the repository CPU training example but removes model downloads, datasets, Hugging Face Trainer, and long training. It uses a deterministic toy model and random-free labels so future agents can check basic bitsandbytes optimizer integration quickly.

Use it for import/training-loop sanity, not for memory benchmarking:

```bash
python sub-skills/optimizers-training/scripts/cpu-optimizer-smoke.py --optimizer adam8bit --steps 3
python sub-skills/optimizers-training/scripts/cpu-optimizer-smoke.py --optimizer adam32bit --steps 3
python sub-skills/optimizers-training/scripts/cpu-optimizer-smoke.py --optimizer adam8bit --force-8bit-small-tensors
```

## Reference-Only Source Scripts

The XPU paged training and paged-memory benchmark examples are not bundled as runnable helpers because they require accelerator hardware, memory-stat APIs, optional Transformers dependencies, and non-trivial model allocation. Their reusable guidance is distilled here: choose `Paged*` classes for memory-pressure accelerator workflows, compare with non-paged classes only under controlled hardware conditions, and record hardware/transfer overhead when interpreting savings.
