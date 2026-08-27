# Module and Configuration Troubleshooting

| Symptom | Likely cause | Recovery |
|---|---|---|
| `TensorforceError.value` for `agent`, `network`, `optimizer`, or module `type` | Unknown registry key or typo | Run `scripts/inspect_module_registry.py`, then replace the key with an installed registry name or import path. |
| Shape/rank errors during model construction | State/action specs do not match network assumptions | Print `environment.states()` and `environment.actions()`; prefer passing the environment to `Agent.create`. |
| Linear normalization warnings | Float state spec lacks `min_value`/`max_value` | Add bounds or choose a different preprocessing path. |
| Keras layer fails to trace/serialize | Custom layer not TensorFlow-compatible or not buildable from Tensorforce graph context | First verify with a simple dense Tensorforce layer; then isolate the custom Keras layer in TensorFlow. |
| TensorFlow Addons import missing | Config references a TFA-dependent component without installing the optional extra | Install a TFA version compatible with the user's TensorFlow, or remove that component. |
| Eager/debug behavior differs from graph mode | `config.eager_mode` or `create_debug_assertions` changed execution | Use eager/debug for diagnosis; retest normal config before performance conclusions. |
