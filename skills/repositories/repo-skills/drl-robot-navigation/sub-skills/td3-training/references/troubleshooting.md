# TD3 training troubleshooting

## `ImportError` for ROS or Gazebo during a model check

**Symptom:** importing the training or environment module fails on `rospy`, ROS
messages, `sensor_msgs`, `gazebo_msgs`, or `roslaunch`; it may also start
`roscore` or create output directories before the requested check.

**Cause:** `train_velodyne_td3.py` imports `GazeboEnv` and performs environment,
writer, and training-loop setup at module scope. `velodyne_env.py` imports ROS
modules and starts subprocesses in `GazeboEnv.__init__`.

**Recovery:** do not import either module for architecture or replay checks.
Use the bundled `td3_model_smoke.py` and `replay_buffer_smoke.py`. If adapting
code, put definitions behind functions or a `__main__` guard and inject the
environment. Report ROS/Gazebo as unverified when unavailable.

## Replay buffer underfill

**Symptom:** the requested batch has fewer rows than expected, or a training
adaptation fails later because it assumes exactly `batch_size` samples.

**Cause:** source `sample_batch(batch_size)` returns every available experience
when `count < batch_size`; it does not pad or raise. A fresh buffer therefore
returns an empty set, and calling tensor/model code on it is not a valid
training step.

**Recovery:** check `buffer.size()` before training and prefill a bounded smoke
with at least the intended batch size. If deliberately testing underfill,
assert the returned first dimension equals `buffer.size()` and stop before
backpropagating. Run `replay_buffer_smoke.py` to check the source contract.

## Checkpoint directory or filename failure

**Symptom:** `torch.save` or `torch.load` reports a missing path, or a later
run cannot find `TD3_velodyne_actor.pth` / `TD3_velodyne_critic.pth`.

**Cause:** source uses relative `./pytorch_models` and assumes the process was
started from `TD3`; it creates `results` always but creates `pytorch_models`
only when `save_model` is true. `save` does not create its directory.

**Recovery:** run from an explicitly selected output root or create both target
directories first. Pass one consistent filename stem and inspect the exact
saved paths. Never write checkpoints into the skill tree or assume a caller's
current directory.

## PyTorch load incompatibility

**Symptom:** a state dictionary fails to load because of device, key, shape, or
serialization/version errors; a broad exception then silently starts random
training in the source.

**Cause:** source calls `torch.load(path)` without `map_location` and catches
all exceptions around loading. It saves only online actor and critic weights,
not optimizer/target state. Newer PyTorch versions may apply different
serialization safety defaults.

**Recovery:** load with explicit `map_location`, inspect keys and tensor shapes,
and report the original exception. For state-dict-only files, use the current
PyTorch-compatible safe loading option where supported, but do not blindly
silence failures or claim a resumed run without verifying parameter equality.
A portable adaptation should record architecture and PyTorch version next to
checkpoints.

## Unexpected TensorBoard location or missing event file

**Symptom:** `tensorboard --logdir runs` shows no scalars, or events appear in a
process-global/default directory rather than the requested output.

**Cause:** `TD3.__init__` creates `SummaryWriter()` with no `log_dir`, so the
location follows the current working directory and TensorBoard's default
behavior. Scalar writes occur once per `train` call, not once per environment
step.

**Recovery:** use an explicit `SummaryWriter(log_dir=chosen_run_dir)` in a
portable adaptation, create the directory, run at least one training call, and
check for an events file. Use the actual run path with TensorBoard. Do not
interpret an empty log as a model failure until you confirm that training was
called.

## Non-finite Q values or invalid target actions

**Symptom:** loss/Q summaries become NaN or actions leave expected bounds.

**Cause:** malformed state/reward fixtures, wrong action scaling, invalid laser
values, or an altered noise/clamp order. The target calculation uses clipped
Gaussian noise followed by action clamping and the minimum of twin Qs.

**Recovery:** inspect finite state/action/reward tensors before training,
confirm `(batch, 24)` and `(batch, 2)`, clamp only at the documented boundaries,
and run the model smoke. Keep `max_action=1` unless the entire action contract
is intentionally changed.

## Near-obstacle branch behaves strangely

**Symptom:** the robot repeatedly reverses/halts linear motion or synthetic
runs show unexplained action plateaus.

**Cause:** when triggered, the source holds one random normalized action for 8–14
steps, forces its first component to `-1`, and uses `state[4:-8]` for the laser
minimum. The condition also requires a random draw above `0.85` and no active
counter.

**Recovery:** log the trigger, counter, sampled action, and laser slice in a
bounded adaptation. Copy the sampled action before forcing its first component
if aliasing matters. Keep this branch optional and do not confuse it with
Gaussian policy noise.

## CUDA selection mismatch

**Symptom:** tensors or checkpoints are placed on different devices, or a
machine without a usable CUDA runtime crashes at startup.

**Recovery:** select `cuda` only when `torch.cuda.is_available()` is true;
otherwise use CPU. Keep all model/input tensors on the same device and use
`map_location` for loading. The bundled smoke defaults to CPU and only tests
CUDA when explicitly requested and available.
