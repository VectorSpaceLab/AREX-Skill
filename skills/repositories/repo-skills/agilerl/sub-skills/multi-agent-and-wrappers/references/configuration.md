# Multi-Agent Configuration

## Agent ID Conventions

Use IDs shaped as `<group_id>_<agent_idx>` when agents are homogeneous by group:

```python
agent_ids = ["speaker_0", "listener_0", "listener_1"]
```

The prefix before `_` can drive group-level network config.

## Single Config For All Agents

Use when all agents have compatible spaces:

```python
net_config = {
    "encoder_config": {"hidden_size": [32, 32], "activation": "ReLU"},
    "head_config": {"hidden_size": [32]},
}
```

## Per-Group Config

Use when homogeneous groups need different architectures:

```python
net_config = {
    "speaker": {"encoder_config": {"hidden_size": [32]}, "head_config": {"hidden_size": [32]}},
    "listener": {"encoder_config": {"hidden_size": [64, 64]}, "head_config": {"hidden_size": [32]}},
}
```

## Per-Agent Config

Use when every agent is different:

```python
net_config = {
    "speaker_0": {"encoder_config": {"hidden_size": [32]}, "head_config": {"hidden_size": [32]}},
    "listener_0": {"encoder_config": {"hidden_size": [64]}, "head_config": {"hidden_size": [32]}},
}
```

## Replay Fields

Multi-agent replay data should keep each field keyed by agent ID and aligned across vectorized env steps. Validate field names and key sets before sampling.
