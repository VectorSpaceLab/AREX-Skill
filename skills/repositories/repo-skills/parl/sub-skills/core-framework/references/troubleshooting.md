# PARL core troubleshooting

Use this reference when core imports, backend aliases, weight transfer, or Agent persistence fail.

## No deep-learning framework found

Symptoms:

- `import parl` succeeds but `parl.Model`, `parl.Algorithm`, or `parl.Agent` is missing.
- A checker reports that no core backend aliases were exported.
- A task can use `parl.remote_class` but cannot build `parl.Model` code.

Likely cause: no supported core backend is importable in the active Python environment.

Fix:

1. Decide the backend needed by the code: `torch`, `paddle`, or `fluid`.
2. Install a compatible backend package for that Python version and platform.
3. Set `PARL_BACKEND` before importing PARL.
4. Re-run alias verification.

```bash
PARL_BACKEND=torch python -c "import parl; print(parl.Model.__module__)"
```

For distributed-only questions, route to `../../xparl-distributed/`, but model and algorithm development still needs a real backend.

## Wrong `PARL_BACKEND`

Symptoms:

- Assertion failure during `import parl`.
- `parl.Model.__module__` points to `parl.core.paddle` when the code uses `torch.nn`.
- Changing `os.environ["PARL_BACKEND"]` in a notebook appears to have no effect.

Fix:

- Use exactly `torch`, `paddle`, or `fluid`; values such as `pytorch`, `paddlepaddle`, `Torch`, or extra spaces are invalid.
- Set the variable before any `import parl` or before importing a module that imports PARL.
- Restart notebooks or long-running interpreters after changing the backend.
- If both Paddle and Torch are installed and the code should be Torch, set `PARL_BACKEND=torch` explicitly because the automatic default prefers Paddle.

## Torch or Paddle is missing

Symptoms:

- `PARL_BACKEND=torch` fails with a message that Torch is not installed.
- `PARL_BACKEND=paddle` fails with `ModuleNotFoundError` or another Paddle import error.
- `PARL_BACKEND=fluid` fails because `paddle.fluid` cannot be imported.

Fix:

- Install the backend matching the code and hardware. CPU packages are sufficient for import, alias, and small framework checks.
- Use Torch for `torch.nn.Module`, `torch.optim`, and `torch.Tensor` code.
- Use Paddle 2.x for `paddle.nn.Layer`, Paddle optimizers, and dynamic graph examples.
- Use Fluid only for legacy static-graph code that explicitly uses `paddle.fluid`, `parl.layers`, and agent `build_program()`.

## NumPy 2 versus older Torch warnings

Symptoms:

- A Torch import or `get_weights()` call warns about NumPy initialization or a module compiled against NumPy 1.x.
- `RuntimeError: Numpy is not available` appears when converting Torch tensors to NumPy arrays.

Why it matters: PARL Torch `Model.get_weights()` converts state-dict tensors to NumPy arrays. Older Torch wheels may not work correctly with NumPy 2.x.

Fix:

- Use a Torch release compatible with the installed NumPy, or pin NumPy to a 1.x release supported by that Torch build.
- After changing NumPy or Torch, restart the Python process and re-run:

```bash
PARL_BACKEND=torch python ../scripts/check_parl_core.py --torch-smoke always
```

## Save/restore misuse

Symptoms:

- Restored predictions differ unexpectedly.
- Restore fails with missing keys, unexpected keys, or shape mismatch.
- Fluid save complains that the path is a file, not a directory.
- Torch restore on CPU fails for a checkpoint saved from GPU tensors.

Fix:

- Recreate the same model class and constructor dimensions before calling `restore`.
- For Torch and Paddle dynamic-graph agents, treat `save_path` as a checkpoint file path.
- For legacy Fluid agents, treat `save_path` as a directory containing program parameter files.
- If the algorithm has multiple models, pass the intended `model=` to `save` / `restore` when supported, or use structured `get_weights` / `set_weights` at the agent or algorithm level.
- For Torch checkpoints produced on GPU, restore with a CPU map location when running on CPU:

```python
agent.restore("model.ckpt", map_location="cpu")
```

## `get_weights` / `set_weights` shape mismatches

Symptoms:

- Assertion that weights are inconsistent with the current algorithm.
- Paddle error that a key expects one shape but received another.
- Torch `load_state_dict` reports missing/unexpected keys or size mismatch.

Fix:

- Copy weights only between equivalent model/algorithm/agent structures.
- Confirm constructor dimensions such as observation size, action size, hidden units, and multi-agent counts are identical.
- Do not pass model-level weights into an agent-level `set_weights` call; agent and algorithm wrappers may expect nested dict/list structures.
- For `AlgorithmBase`, remember that direct model attributes and first-level lists/tuples/dicts of models are included; models nested deeper inside containers are not automatically traversed.

## `sync_weights_to` fails

Symptoms:

- Assertion `cannot copy between identical model`.
- Assertion that models must be the same class.
- Soft update produces unexpected outputs.

Fix:

- Create a separate target instance, usually with `copy.deepcopy(model)` or the same constructor.
- Keep source and target class names and parameter structures identical.
- Use `decay=0.0` for a hard copy. Use a value in `[0, 1]` for target-network soft updates.
- Ensure both models have initialized parameters before synchronization.

## Missing `forward`, `policy`, or `value` method

Symptoms:

- Algorithm code asserts that a model needs to implement a named method.
- Agent prediction fails because the model is not callable.
- Inference export fails because `forward` is not implemented.

Fix:

- Implement the method expected by the algorithm recipe. DQN-style code often uses `value(obs)`; policy-gradient style code often uses `policy(obs)`; generic Torch/Paddle modules should implement `forward(obs)`.
- For Paddle `save_inference_model`, the model must have a real `forward` method and matching input shape/dtype lists.
- If choosing or adapting a specific RL algorithm, route to `../../algorithm-recipes/`.

## Editable local install issue

Symptoms:

- `import parl` works from inside a checkout but fails from another directory.
- Package metadata says PARL is installed, but imports resolve incorrectly.
- An editable install of a legacy `setup.py` project behaves differently across packaging tool versions.

Fix:

- Prefer a regular installed wheel when editing the PARL source is not needed.
- If editable development is required, use a compatibility-mode editable install supported by your packaging frontend, then validate imports from outside the repository directory.
- Confirm the public version and backend aliases with the bundled checker or a minimal `python -c` command.

## When to route elsewhere

- Built-in algorithm choice, loss/update details, or example training loops: `../../algorithm-recipes/`.
- xparl cluster start/connect/status/stop, remote class behavior, serialization, or security: `../../xparl-distributed/`.
- Gym API compatibility, replay memory, schedulers, CSV logging, tensorboard/visualdl summaries, or wrappers: `../../environment-utils/`.
