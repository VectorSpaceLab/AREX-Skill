# Architecture Configuration

## MLP Config

```python
net_config = {
    "encoder_config": {
        "hidden_size": [64, 64],
        "activation": "ReLU",
        "min_mlp_nodes": 16,
        "max_mlp_nodes": 128,
    },
    "head_config": {"hidden_size": [64]},
}
```

## CNN Config

```python
net_config = {
    "encoder_config": {
        "channel_size": [32, 64, 128],
        "kernel_size": [8, 4, 3],
        "stride_size": [4, 2, 1],
        "activation": "ReLU",
    },
    "head_config": {"hidden_size": [64]},
}
```

Check image channel ordering. If observations arrive as `[H, W, C]`, use AgileRL utilities or configuration flags to convert to `[C, H, W]` when required.

## Multi-Input Config

Use for Dict/Tuple observations with multiple modalities.

```python
net_config = {
    "encoder_config": {
        "latent_dim": 32,
        "mlp_config": {"hidden_size": [32, 32]},
        "cnn_config": None,
        "lstm_config": None,
        "vector_space_mlp": True,
    },
    "head_config": {"hidden_size": [64]},
}
```

## LSTM/Recurrent Config

Use LSTM configs for partially observable environments or sequence tasks. Validate hidden-state shape, sequence length, and reset behavior before training.

## Mutation Bounds

Set mutation bounds (`min_*`, `max_*`) to realistic ranges. Very wide bounds can create architectures that are too large or incompatible with resource limits.
