---
name: atari-and-asl-workflows
description: "Routes DRL-Pytorch Atari Noisy/Dueling/Double DQN, NoFrameskip,
  EnvIdex, wrapper, checkpoint, EnvPool, and Actor-Sharer-Learner workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Atari and ASL Workflows

Use this sub-skill when the request involves DRL-Pytorch Atari workflows:
Pong, Enduro, `NoFrameskip`, `AtariNames`, `EnvIdex`, Noisy/Dueling/Double
DQN flags, pretrained Atari checkpoints, Tianshou-style preprocessing wrappers,
ALE ROM/license/OpenCV gates, EnvPool, or Actor-Sharer-Learner (ASL)
multiprocessing.

## Route here for

- Atari DQN training, evaluation, or checkpoint-loading commands under the
  Noisy/Duel/DDQN Atari workflow.
- Mapping `--EnvIdex` to Atari game names, especially `37 -> Pong` and
  `20 -> Enduro`.
- Combining `--Double`, `--Duel`, and `--Noisy` flags and matching them to
  checkpoint filenames.
- Explaining the Atari wrapper stack that returns `torch.uint8` observations of
  shape `(4, 84, 84)`.
- Diagnosing missing ALE ROMs, missing OpenCV, display/render failures, default
  CUDA-device failures, and optional EnvPool installation problems.
- Understanding ASL process roles: Actor, Sharer, Learner, Evaluator, and
  Recorder.

## Route away

- Non-Atari CartPole, LunarLander, CliffWalking, PER, C51, or NoisyNet DQN
  requests belong to the `value-based-discrete-control` sibling.
- PPO, DDPG, TD3, SAC, Pendulum, MuJoCo, Box2D continuous-control, or other
  non-Atari actor-critic requests belong to the `policy-and-actor-critic-control`
  sibling.
- Full training benchmark recovery, ROM acquisition, license acceptance,
  heavyweight downloads, and checkpoint binary bundling are outside this
  sub-skill's safe default behavior.

## Read first

- [Atari runtime and wrappers](references/atari-runtime-and-wrappers.md) for
  `EnvIdex` mapping, Pong/Enduro commands, algorithm flag combinations,
  wrapper order, checkpoint naming, and optional dependency gates.
- [ASL framework](references/asl-framework.md) for the EnvPool ASL topology,
  process responsibilities, major flags, device placement, and safe runtime
  boundaries.
- [Troubleshooting](references/troubleshooting.md) when a task mentions ALE,
  ROMs, `cv2`, EnvPool, CUDA, multiprocessing hangs, rendering, long training,
  or checkpoint load failures.
- [smoke_atari_asl.py](scripts/smoke_atari_asl.py) for a CPU-only diagnostic
  that imports the Atari Agent and ASL utility modules from a user-supplied
  DRL-Pytorch checkout, runs dummy CNN forwards, and optionally probes wrapper
  or EnvPool imports without creating Atari ROM environments.

## Safe operating flow

1. Identify whether the user wants the Atari DQN workflow or the ASL EnvPool
   framework. The Atari DQN workflow uses `Name[EnvIdex] + "NoFrameskip-v4"`;
   ASL uses `Name[EnvIdex] + "-v5"` with EnvPool.
2. Resolve `EnvIdex`: use `37` for Pong and `20` for Enduro unless the user
   explicitly names another game from the bundled Atari table.
3. Check gates before suggesting execution:
   - Atari DQN environment creation needs Gymnasium Atari support, accepted ALE
     ROM licensing, and OpenCV for frame warping.
   - ASL needs EnvPool on a supported platform plus Atari environment support;
     it launches multiple processes and is not a quick smoke.
   - CUDA is optional acceleration, but several launchers default to CUDA; set
     CPU device flags explicitly for CPU-only diagnostics.
4. For a no-ROM diagnostic, run the bundled smoke script, for example:

   ```bash
   python sub-skills/atari-and-asl-workflows/scripts/smoke_atari_asl.py --repo-root <repo-root>
   ```

   Add `--probe-atari-wrappers` or `--probe-envpool` only when diagnosing those
   optional imports. The script does not create Atari environments, download
   ROMs, start EnvPool workers, or run training.
5. For real Atari commands, use the copied command facts in the references and
   warn about side effects: environment creation, rendering, TensorBoard writes,
   checkpoint reads/writes, long training loops, and multiprocessing.

## Output expectations

- Give commands with explicit `--EnvIdex`, algorithm toggles, and device flags.
- State whether a proposed command is a safe diagnostic, an environment-creation
  check, or a real training/rendering run.
- Match checkpoint names to the exact `ExperimentName` convention before
  loading: algorithm prefix plus Atari environment name plus `_<ModelIdex>k.pth`.
- Do not claim optional ROM/OpenCV/EnvPool/CUDA runtime has been verified unless
  the current user environment was actually probed for that task.
