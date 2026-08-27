# Evolvable API Reference

## Config Objects

Verified constructor examples include:

```python
MlpNetConfig(hidden_size: list[int], activation="ReLU", output_activation=None, ...)
CnnNetConfig(channel_size: list[int], kernel_size: list[int | tuple[int, ...]], stride_size: list[int], ...)
LstmNetConfig(hidden_state_size: int, num_layers=1, dropout=0.0, ...)
SimBaNetConfig(hidden_size: int, num_blocks: int, output_activation=None, ...)
```

Use config objects when you want validated, structured network configuration; use dictionaries when following demos/YAML patterns.

## Modules

- `agilerl.modules.base.EvolvableModule`
- `agilerl.modules.mlp.EvolvableMLP`
- `agilerl.modules.cnn.EvolvableCNN`
- `agilerl.modules.lstm.EvolvableLSTM`
- `agilerl.modules.multi_input.EvolvableMultiInput`
- `agilerl.modules.simba.EvolvableSimBa`
- `agilerl.modules.dummy.DummyEvolvable`

## Networks

- `agilerl.networks.q_networks.QNetwork`
- `agilerl.networks.q_networks.RainbowQNetwork`
- `agilerl.networks.q_networks.ContinuousQNetwork`
- `agilerl.networks.value_networks.ValueNetwork`
- `agilerl.networks.actors.DeterministicActor`
- `agilerl.networks.actors.StochasticActor`

## Utilities

`agilerl.utils.evolvable_networks` contains helpers for activation lookup, encoder defaults, MLP/CNN/SimBa/ResNet construction, image/vector space detection, and tuple-to-dict conversions.

When signatures are hidden by AgileRL metaclasses, inspect the source or instantiate via documented examples rather than relying on `inspect.signature` alone.
