# FSDP CPU Offloading for Large ESM-2 Inference

Use this reference when a user needs ESM-2 15B embeddings or contacts and normal GPU inference runs out of memory. This is a reference-only workflow because it depends on external packages, CUDA, distributed initialization, and model downloads.

## When to Use

Consider FSDP CPU offload when all are true:

- The target model is very large, especially `esm2_t48_15B_UR50D`.
- A CUDA GPU is available but cannot hold the full model normally.
- Installing/importing `fairscale` is acceptable.
- Distributed initialization with a single local rank is acceptable.
- Model weight downloads or cached weights are available.

For quick checks or CPU-only environments, prefer smaller ESM-2 models instead.

## Dependency Expectations

The reference pattern uses:

- PyTorch with CUDA support.
- `fairscale.nn.data_parallel.FullyShardedDataParallel`.
- `fairscale.nn.wrap.enable_wrap` and `wrap`.
- Torch distributed initialized with world size `1`.

Do not promise this path in minimal environments. It is not needed for `esm-extract --help`, alphabet checks, or small model command construction.

## Pattern

```python
import torch
from fairscale.nn.data_parallel import FullyShardedDataParallel as FSDP
from fairscale.nn.wrap import enable_wrap, wrap
import esm

torch.distributed.init_process_group(
    backend="nccl",
    init_method="tcp://localhost:23456",
    world_size=1,
    rank=0,
)

model_name = "esm2_t48_15B_UR50D"
model_data, regression_data = esm.pretrained._download_model_and_regression_data(model_name)
fsdp_params = dict(
    mixed_precision=True,
    flatten_parameters=True,
    state_dict_device=torch.device("cpu"),
    cpu_offload=True,
)

with enable_wrap(wrapper_cls=FSDP, **fsdp_params):
    model, alphabet = esm.pretrained.load_model_and_alphabet_core(
        model_name, model_data, regression_data
    )
    converter = alphabet.get_batch_converter()
    model.eval()

    for name, child in model.named_children():
        if name == "layers":
            for layer_name, layer in child.named_children():
                setattr(child, layer_name, wrap(layer))
    model = wrap(model)
```

After wrapping, tokenize sequences normally, move tokens to CUDA, and run inference under `torch.no_grad()`:

```python
labels, seqs, tokens = converter([("protein", "MKTVRQERLKSIVRIL")])
tokens = tokens.cuda()
with torch.no_grad():
    results = model(tokens, repr_layers=[48], return_contacts=True)
```

## Caveats

- CPU offload reduces GPU memory pressure but can be slower and still requires enough host RAM.
- The sample distributed URL/port must not conflict with another process.
- This path is for inference; do not adapt it blindly for training.
- If contact predictions are not needed, set `return_contacts=False` to reduce attention-related memory pressure.
- If FSDP setup fails, fall back to a smaller model before attempting broad dependency changes.
