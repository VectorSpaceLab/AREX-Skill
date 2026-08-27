# Package-wide troubleshooting

Use this page for install/import/backend triage before opening a workflow-specific troubleshooting file.

## Import fails before any agent code runs

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'rl'` | `keras-rl` distribution is not installed in the active Python. | Install `keras-rl`, then rerun the minimal import check from the root skill. |
| `ModuleNotFoundError: No module named 'keras'` | Standalone Keras dependency is missing. | Install a legacy Keras 2.x-compatible stack; do not substitute modern Keras 3 unless a smoke check proves compatibility. |
| `ModuleNotFoundError: No module named 'wandb'` while importing callbacks or agents | This version imports `wandb` from `rl.callbacks` at module import time. | Install a compatible `wandb`, or patch/avoid callback imports only if the user is maintaining a local fork. For ordinary package use, installing W&B is usually simpler. |
| TensorFlow protobuf descriptor errors | TensorFlow 1.x with too-new `protobuf`. | Use a protobuf version compatible with the TensorFlow wheel, or choose a different legacy backend stack. |
| Theano native-op errors such as `undefined symbol: dgemm_` | Theano compiled a BLAS-backed extension but no compatible BLAS library was linked in the environment. | Install/link a BLAS runtime such as OpenBLAS in the environment, clear or redirect the Theano compiledir, and rerun a compile smoke. |

## Agent construction fails after imports succeed

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| Error around `len(model.output)` or symbolic tensor shape | Legacy keras-rl symbolic-output checks disagree with the selected TensorFlow/Keras backend. | Try a legacy backend known to support the old Keras tensor behavior, or patch the compatibility check if maintaining a fork. Run a compile-only smoke before training. |
| DQN says model output has invalid shape | Final Dense layer width does not equal `nb_actions`, or the model has multiple outputs. | Rebuild the model with exactly one output and final shape `(None, nb_actions)`. See `discrete-control`. |
| DDPG compile or constructor complains about inputs | `critic_action_input` is not the exact action `Input` used by the critic, or actor/critic shapes do not match action/observation spaces. | See `continuous-control` and run its smoke helper with negative diagnostics. |
| NAF shape errors | `L_model` output size or `mu_model` output shape does not match `nb_actions` and covariance mode. | See the NAF API/workflow references in `continuous-control`. |

## Fit/test lifecycle failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `Please call compile() before fit()` or before `test()` | Agent was constructed but not compiled. | Compile the agent first. DQN/SARSA/DDPG/NAF need optimizer(s); CEM uses `compile()` with no arguments. |
| `action_repetition must be >= 1` | Invalid lifecycle argument. | Use an integer >= 1. |
| Rendering/display errors with `visualize=True` | Headless environment or missing display/OpenGL support. | Run with `visualize=False`; use saved logs instead of live rendering. |
| Gym reset/step unpacking errors | New Gym/Gymnasium API returns `(obs, info)` from reset or `(obs, reward, terminated, truncated, info)` from step. | Add a compatibility wrapper that adapts to old Gym `(obs)` and `(obs, reward, done, info)` signatures expected by keras-rl. |

## Optional workflow blockers

| Workflow | Blocker | Safe response |
| --- | --- | --- |
| Atari DQN | Atari ROM/data setup, Pillow, old Gym Atari extras, long training, possible display rendering. | Use the bundled Atari processor reference; only install/run Atari extras after explicit user approval. |
| MuJoCo DDPG | MuJoCo system packages/license and long training. | Keep MuJoCo guidance reference-only unless the user has prepared the simulator. |
| Weight save/load | Missing or incompatible `h5py`. | Install an `h5py` version compatible with the chosen Keras stack; test saving to a temporary file before long training. |
| W&B logging | Missing package or W&B credentials/network. | Install W&B for imports, but do not start online logging unless the user provides credentials and asks for it. |

## Where to go next

- Discrete-agent construction, memory/policy choice, DQN/SARSA/CEM shape issues: `sub-skills/discrete-control/references/troubleshooting.md`.
- DDPG/NAF actor-critic wiring, random processes, MuJoCo/Pendulum caveats: `sub-skills/continuous-control/references/troubleshooting.md`.
- `fit`/`test`, processors, callbacks, FileLogger, W&B, log plotting, environment checks: `sub-skills/core-extension-and-logging/references/troubleshooting.md`.
