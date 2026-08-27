# Atari and ASL Troubleshooting

## Purpose

Use this reference when DRL-Pytorch Atari DQN or ASL requests fail around ROMs,
OpenCV, EnvPool, device defaults, multiprocessing, rendering, training length,
checkpoint names, or import-path collisions. Start with the no-ROM diagnostic
unless the user explicitly wants to create Atari environments:

```bash
python sub-skills/atari-and-asl-workflows/scripts/smoke_atari_asl.py --repo-root <repo-root>
```

## Failure matrix

| Symptom or error fragment | Likely cause | Recovery |
|---|---|---|
| `Namespace ALE not found`, `No registered env`, `PongNoFrameskip-v4` not found, or an Atari env fails before reset | Gymnasium Atari support or accepted ALE ROMs are missing | Do not treat this as a model bug. Install the Atari Gymnasium extra and accept ROM licensing through the user's approved process. This skill does not download ROMs or accept licenses. Use the bundled smoke script to validate CNN imports without ROMs. |
| `ModuleNotFoundError: No module named 'cv2'` | The Tianshou-style wrapper imports OpenCV at module import time | Install `opencv-python` if the user intends to use the wrapper stack. Without OpenCV, avoid `--probe-atari-wrappers` and real Atari environment creation; the core Atari Agent dummy forward can still be checked. |
| Wrapper assertion mentions `NoFrameskip` | The Atari DQN wrapper requires an env name containing `NoFrameskip` | Use `Name[EnvIdex] + "NoFrameskip-v4"` for the Atari DQN workflow, not `Pong-v5` or a non-Atari Gym env. `Pong-v5` belongs to ASL/EnvPool. |
| Assertion involving `NOOP` or `FIRE` action meanings | The wrapper assumes Atari ALE action semantics | Confirm the environment is an ALE Atari env and the ROM is supported. Disable `--noop_reset` if only the `NOOP` assertion is involved, but do not bypass `FIRE` assumptions for games that require reset firing. |
| `ModuleNotFoundError: No module named 'envpool'` | ASL's launcher and Actor/Evaluator import EnvPool | Install EnvPool only when the user intentionally runs ASL. EnvPool is optional for Atari DQN and for the bundled dummy smoke. Use `--probe-envpool` to distinguish an import problem from a runtime environment problem. |
| EnvPool install fails or no compatible wheel exists | Platform, Python, or binary compatibility mismatch | ASL was documented for Ubuntu-like Linux hosts. On unsupported platforms, route to Atari DQN or non-Atari sibling workflows rather than forcing ASL. Do not claim ASL has been verified if only base PyTorch/Gymnasium imports work. |
| `Torch not compiled with CUDA enabled`, `CUDA unavailable`, or device transfer failure | The launchers default to CUDA-oriented devices | For Atari DQN pass `--device cpu`. For ASL pass all process devices explicitly: `--A_dvc cpu --B_dvc cpu --L_dvc cpu --E_dvc cpu`. If using CUDA replay, ensure `--B_dvc` equals `--L_dvc`. |
| ASL assertion `B_dvc == L_dvc` fails | CUDA replay buffer and Learner devices differ | Use `--B_dvc cpu` for RAM replay, or set both `--B_dvc` and `--L_dvc` to the same CUDA device. |
| ASL assertion `buffersize >= explore_steps` fails | Replay capacity is smaller than the random exploration phase | Increase `--buffersize` or lower `--explore_steps`. The default is `buffersize=1000000`, `explore_steps=150000`, which satisfies the assertion. |
| Multiprocessing appears hung, especially from notebooks or shells | ASL uses `mp.set_start_method('spawn')`, a Manager process, EnvPool workers, evaluators, and a Recorder that sleeps | Run ASL as a script from a normal shell, not inside an interactive notebook. Start with fewer `--train_envs` and CPU devices for diagnosis. Expect the Recorder to poll every 60 seconds and shutdown delays after other processes join. Clean up child processes if interrupted. |
| ASL Actor seems to wait even though the GPU is idle | Time Feedback Mechanism is balancing actor and learner step times | Disable with `--time_feedback False` only when diagnosing scheduler behavior. Otherwise, wait behavior can be intentional when actor collection is faster than learner optimization or vice versa. |
| `--render True` opens no window, hangs, or fails with display errors | Human render mode needs a GUI/display; render mode loops evaluation indefinitely | Prefer `--render False` for training and diagnostics. Use a virtual display only when rendering is the actual user goal. Interrupt the render loop manually after enough frames. |
| A supposedly quick Atari command still fails on ROMs or takes time | `--Max_train_steps 0` skips the training loop but still constructs evaluation and training environments | Use the bundled smoke script for no-ROM checks. Only use `--Max_train_steps 0` after Atari dependencies and ROMs are available and the user wants an environment-construction check. |
| Training appears slow or no learning is visible soon | Defaults are long and stochastic: Atari DQN `Max_train_steps=1e6`, ASL `max_train_steps=5e7`, replay warmups, vectorized EnvPool, and periodic evaluation | Clarify whether the user wants a smoke, a debugging run, or a real experiment. Do not promise benchmark scores from short runs. Reduce steps and env counts only for diagnostics, not for final performance claims. |
| `FileNotFoundError` while loading `.pth` or model loads the wrong weights | Checkpoint name is tied to algorithm flags, environment suffix, and `ModelIdex` | Reconstruct `ExperimentName = algo_name + '_' + EnvName`. Example: Enduro Double-Duel DQN at `--ModelIdex 900` expects `Double-Duel-DQN_EnduroNoFrameskip-v4_900k.pth`. Confirm current working directory and that checkpoint binaries are user-provided. |
| `RuntimeError` with missing/unexpected keys in checkpoint | Checkpoint was trained with different `--Duel`, `--Noisy`, `--fc_width`, or action dimension | Match the architecture flags and environment before loading. Dueling and Noisy variants change module names and layer types, so state dicts are not interchangeable. |
| `KeyError` for `EnvIdex` | Env index outside `1..57` or mistyped flag | Use the bundled Atari table. Pong is `37`; Enduro is `20`; ASL default Alien is `1`. |
| Importing `utils` gives the wrong `Q_Net`, `NoisyLinear`, or `str2bool` | Both Atari DQN and ASL directories define `utils.py` and `AtariNames.py` | Isolate imports by workflow directory. The bundled smoke script purges conflicting module names between imports; use it as a pattern for diagnostics. |
| Invalid boolean CLI values behave strangely | DRL-Pytorch uses custom `str2bool` parsers | Pass explicit values from the accepted set, such as `True`, `False`, `1`, or `0`. Avoid ambiguous values like `yesplease` or `maybe`. |
| TensorBoard logs overwrite or create unexpected directories | Atari DQN writes under `runs/{ExperimentName}_S{seed}...`; ASL writes under `runs/ASL_S{seed}_big_{ExpEnvName}...` | Set `--write False` for diagnostics. If logging is desired, run from the intended workflow directory and archive old runs first. |

## Minimal triage sequence

1. Identify workflow: Atari DQN uses `NoFrameskip-v4`; ASL uses EnvPool `-v5`.
2. Run the no-ROM bundled smoke script to check base PyTorch module imports and
   dummy CNN forwards.
3. If wrapper imports are the issue, rerun with `--probe-atari-wrappers` and
   check for `cv2` or Gymnasium Atari import failures.
4. If ASL is the issue, rerun with `--probe-envpool`; missing EnvPool is an
   optional ASL gate, not a failure of non-ASL workflows.
5. Only after optional gates are satisfied, run real environment-construction or
   training commands with explicit device flags and intentionally chosen
   `EnvIdex`.

## Stop conditions

Stop and ask the user before:

- Downloading ROMs, accepting ROM licenses, installing large optional extras, or
  changing system packages.
- Launching ASL multiprocessing training on shared machines.
- Running long training loops or rendering loops when the user only asked for a
  diagnosis.
- Claiming pretrained play works without the expected checkpoint binary in the
  workflow's `model/` directory.
