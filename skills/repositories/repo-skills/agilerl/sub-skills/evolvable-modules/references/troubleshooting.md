# Evolvable Module Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| CNN shape error | Kernel/stride too large for input, wrong channel order, or missing sample input | Verify image shape, channel order, kernel sizes, and `sample_input` when needed. |
| Dict/Tuple observation fails | MultiInput config missing a modality config or vector-space handling | Define `mlp_config`, `cnn_config`, `lstm_config`, and `vector_space_mlp` deliberately. |
| Architecture mutation does nothing | Module not registered as evolvable or mutation probability disabled | Use `EvolvableModule`/`EvolvableNetwork` and check HPO mutation config. |
| Custom PyTorch module fails in AgileRL algorithm | It does not expose expected evolvable interface | Wrap with `DummyEvolvable` or implement an `EvolvableModule` subclass. |
| Output action shape mismatch | Actor/Q-network head does not match action space | Recheck `action_space`, head output dimensions, and continuous vs discrete algorithm choice. |
| Recurrent workflow has hidden-state errors | LSTM config and training loop sequence handling disagree | Start with a tiny recurrent smoke test and validate reset/hidden-state dimensions. |

## Debug Checklist

1. Print observation/action spaces.
2. Build the smallest MLP config first.
3. Instantiate the network or population without training.
4. Run one forward pass with a tiny synthetic observation.
5. Add CNN/LSTM/MultiInput complexity after shape checks pass.
6. Add architecture mutation only after construction and forward pass are stable.
