# Module Authoring Troubleshooting

| Symptom | Cause | Recovery |
| --- | --- | --- |
| `module.trainable_variables` is empty | The module has not been called or the forward path did not touch variable-creating code. | Call with representative tensors or `snt.build` before inspecting variables. |
| `@snt.once` method returns a tensor/value | Sonnet's once-decorated methods are side-effect-only. | Store created objects on `self`; return `None`. |
| Shape error during first call | Input-dependent variable dimensions are unknown or incompatible. | Assert static final dimension before variable creation; run a small smoke input. |
| Variables are recreated or duplicated | Variable creation happens directly in `__call__` instead of under `@snt.once` or a child module. | Move creation into `__init__`, a child module, or `@snt.once`. |
| `Sequential` cannot pass `is_training` or multiple tensors | `Sequential` is a simple one-output chain. | Write an explicit `snt.Module` with a custom `__call__`. |
| Checkpoint/SavedModel misses variables | The module was saved before being built. | Run a representative call before saving; then use the serialization sub-skill. |
