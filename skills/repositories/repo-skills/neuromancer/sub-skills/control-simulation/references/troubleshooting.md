# Control simulation troubleshooting

Use the smallest failing fixture and print keys, shapes, dtype, device, seed,
and horizon before changing the model. The table below separates diagnosis
from recovery; do not hide a required data, network, or hardware prerequisite.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `KeyError` for `X` or another horizon key | `nsteps=None` and the default `nstep_key='X'` is absent, or a node is ordered before its producer | Supply the key as rank-3 data or set `nsteps`/`nstep_key` explicitly; order nodes producer-first; print each node's input/output keys. |
| Indexing error at `data[key][:, i]` | A rollout value is 1-D/2-D instead of `(B,T,F)`, or `T` is shorter than the requested horizon | Add a batch and time axis, use an `init_func` for the initial state, and make every time-bearing exogenous input at least `N` samples long. |
| State has `N+1` samples but action has `N`, or a reference has a different length | Recurrent state starts with one sample; generated outputs are appended while supplied inputs are retained | Treat `X` as initial-plus-predictions and `U` as per-step actions. Align objectives with the intended slice instead of padding outputs blindly. |
| `System` constructs but forward raises a missing intermediate key | Nodes are not topologically ordered for the current-step dataflow | Put policy/disturbance nodes before the plant, and plant output before downstream observation nodes. A graph picture alone does not repair execution order. |
| Duplicate-name graph collision or assertion | Two nodes share `name`, including an empty name after normalization; graph construction does not catch every collision | Give every node an explicit unique name. Preview maps must use those exact names. |
| Node output is missing a declared key | Callable returned one tensor or a shorter tuple; `Node` zips outputs and does not synthesize missing values | Return a tuple with exactly the intended arity and assert the result keys in a smoke. |
| Preview policy has a matrix-width error | Preview is flattened from `(B,1+L,F)` to `(B,(1+L)*F)` but the policy was sized for only `F` | Set `insize` to current widths plus `(L+1)*F`; test the first and final windows. |
| Preview fails near the sequence end | No future samples remain, a padding mode is invalid for the sequence, or `preview_length` was inferred from `None` | Set explicit `preview_length`; choose `replicate`, `constant`, `circular`, or `reflect` intentionally; make the input rank-3 and long enough for the current index. |
| `constant` preview padding ignores the requested value | `pad_constant` is only used when `pad_mode='constant'` | Set both `pad_mode='constant'` and `pad_constant=<value>`. Other modes deliberately ignore the constant. |
| Moving-horizon output is unexpectedly 3-D or history leaks between episodes | The wrapper stacks `(ndelay,B,F)` and keeps mutable history | Reduce/select a history result inside the wrapped callable if needed; recreate or clear `history` for each episode and verify batch/device compatibility. |
| PSL simulation is unexpectedly slow at construction | `EmulatorBase(set_stats=True)` runs a default statistics simulation; a domain model may also use a long default horizon | Start with `set_stats=False`, `nsim=2..10`, explicit `x0`/`U`, and add statistics only after the short path passes. |
| Non-autonomous `U` length or time is off by one | Controls are interpolated with an internal time vector and outputs omit the initial integration sample | Supply the documented extra leading control sample (`U[:nsim+1]` for an `nsim` rollout), then assert returned row counts. Do not compare raw `U` and `X` without checking their conventions. |
| NumPy and Torch PSL results disagree | Different initial conditions/seeds, float32 casting, backend-specific equations, or a host/device conversion | Use the same explicit `x0`, controls, seed, and short horizon; compare with tolerance; keep the first parity check on CPU. |
| `Backend` or emulator complains about dtype/device | Torch and NumPy values were mixed, or a tensor is on an unsupported device | Cast all inputs to the chosen backend and dtype before simulation. Treat external interpolation that converts to NumPy as CPU-only unless separately verified. |
| Normalization raises a type lookup error or returns bad values | Scaler stats and input type do not match, a constant channel has zero std, or a dictionary key has no scaler | Use NumPy arrays with NumPy stats or Torch tensors with Torch-compatible stats; add epsilon to zero std; normalize only keys with known stats and preserve `Time` as excluded when appropriate. |
| `requests` import is unavailable | Some package/distribution metadata does not declare the PSL base module's imported helper | Repair the isolated package environment or use a local, no-download path. Do not add an implicit download to a skill smoke. |
| `FileEmulator` rejects a local file | Unsupported extension, no `X`/`Y`, missing numeric prefixes, inconsistent row counts, or malformed `exp_id`/`Time` | Use `.csv` or `.mat`; validate `xN/yN/uN/dN` names and dimensions; supply a local path and a short `nsim`. |
| Building or file-backed system tries to access the network | No local parameter/data file was supplied, so the registry path invoked its download helper | Stop if network/data is not authorized. Acquire the required file separately, pass its local path where supported, and record the prerequisite. |
| GPU run fails or runs out of memory | CUDA is optional for this graph; device, driver, extension, or memory was not verified | Reproduce on CPU with a tiny horizon. Report CUDA as optional/unverified rather than treating importability as successful execution. |
| Control example takes too long or creates plots/checkpoints | Repository examples include training, long horizons, domain data, and plotting side effects | Distill the node/rollout recipe, use the bundled deterministic smoke, and run only a bounded native test when explicitly approved. |
| DPC loss is non-finite or policy gradients are absent | Detached model path, wrong state/reference shape, excessive horizon, unbounded action, or objective keys do not match rollout keys | First verify a 2–4 step forward and `requires_grad` on policy parameters; check output keys/shapes, bound actions, lower the horizon, and only then add objectives/constraints. |

## Quick isolation sequence

1. Run `python scripts/simulation_smoke.py --help`, then `--run` in an
   environment containing the package.
2. Replace the real policy and plant with identity/additive lambdas while
   preserving keys and axes.
3. Add one node at a time, asserting `(B,F)` at its callable boundary and the
   cumulative `(B,T,F)` shape after the system.
4. Add preview or moving history only after the ordinary `System` passes.
5. Add PSL backend/normalization and compare a short explicit trajectory.
6. Add data, constraints, trainer, plotting, GPU, or external files last.

A failed optional step is a known gap, not a passing result. Keep the CPU smoke
and the unresolved prerequisite separately documented.
