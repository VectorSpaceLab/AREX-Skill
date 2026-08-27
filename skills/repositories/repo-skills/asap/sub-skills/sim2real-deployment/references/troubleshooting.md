# Deployment Troubleshooting

Use this reference when sim2sim, sim2real, joystick control, ROS2/Unitree communication, or data collection fails. Prefer the safe doctor script before starting real hardware.

```bash
python sub-skills/sim2real-deployment/scripts/deployment_doctor.py --repo-root <asap-checkout> --mode sim2sim --config sim2real/config/g1_29dof_hist.yaml
```

## Missing ROS2 or Unitree SDK

Symptoms:

- `ModuleNotFoundError: No module named 'rclpy'`
- `ModuleNotFoundError: No module named 'unitree_sdk2py'`
- Simulator or policy exits before opening a viewer or receiving low state.

Why it happens:

- `sim_env/base_sim.py`, `base_policy.py`, `state_publisher.py`, and `listener_deltaa.py` all import ROS2 and/or Unitree SDK modules.
- Sim2sim also needs these packages because MuJoCo communicates with the policy through Unitree-style DDS topics.

Recovery:

```bash
# In the deployment environment
conda config --env --add channels conda-forge
conda config --env --add channels robostack-staging
conda config --env --remove channels defaults || true
conda install ros-humble-desktop

git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
cd unitree_sdk2_python
pip install -e .
pip install --upgrade numpy scipy
```

Then re-run the doctor. If `rviz2` does not start, fix ROS2 before attempting sim2real.

## Missing Policy Runtime Packages

Symptoms:

- `ModuleNotFoundError` for `onnxruntime`, `sshkeyboard`, `pygame`, `pynput`, `termcolor`, `scipy`, or `yaml`.
- Keyboard listener never starts.
- Joystick mode exits with `No gamepad detected.`

Recovery:

```bash
cd sim2real
pip install -e .
# Add optional packages not declared by sim2real/setup.py but imported by selected paths:
pip install pygame sshkeyboard pynput onnxruntime termcolor scipy pyyaml
```

Notes:

- `sim2real/setup.py` declares `mujoco`, `pyyaml`, `scipy`, `torch`, `onnxruntime`, `pynput`, `ipdb`, and `termcolor` but not `pygame` or `sshkeyboard`.
- `BasePolicy` imports `pygame`, `sshkeyboard`, and `onnxruntime` at module import time, so missing optional input packages can block even keyboard-only policy startup.

## Real Hardware and DDS/Network Failures

Symptoms:

- Policy repeatedly prints `No robot state data received, skipping rl inference`.
- `state_publisher.py` prints `Waiting for low state`.
- Commands appear to run but the robot never responds.
- Sim2sim policy does not see MuJoCo low state.

Checks:

```bash
ip -o -4 addr show
```

Expected interface choices:

- Sim2sim: `INTERFACE: "lo"` on Linux or `"lo0"` on macOS.
- Sim2real: `INTERFACE` must be the Ethernet interface whose IP is in the Unitree subnet, commonly `192.168.123.xxx`.

Recovery:

1. Confirm all processes use the same `DOMAIN_ID`.
2. Confirm `INTERFACE` exists on the current host.
3. For real G1, confirm low-level mode and Ethernet wiring before starting the policy.
4. For sim2sim, start `sim_env/base_sim.py` before the policy terminal and keep both on localhost.
5. Re-run the doctor with `--mode sim2real` to catch `INTERFACE: lo` or missing Unitree subnet before hardware startup.

## MuJoCo Viewer or Display Failures

Symptoms:

- GLFW/display errors.
- `mujoco.viewer.launch_passive` fails.
- Viewer opens but immediately closes.

Recovery:

- Use a machine/session with a working display for interactive sim2sim playback.
- On Linux headless hosts, try a supported MuJoCo GL backend before starting the simulator:

  ```bash
  export MUJOCO_GL=egl      # GPU/EGL hosts
  # or
  export MUJOCO_GL=osmesa   # CPU software rendering if installed
  ```

- Do not switch from failed sim2sim to real hardware as a workaround; fix display or use a different host.

## Joystick Missing or Wrong Mapping

Symptoms:

- `No gamepad detected.`
- Stick axes are inverted or buttons do not match the control map.
- `pygame.error` during joystick initialization.

Recovery:

1. Set `USE_JOYSTICK: 0` to return to keyboard control.
2. Test the gamepad from `sim2real/`:

   ```bash
   python utils/test_xbox.py
   ```

3. Set `JOYSTICK_TYPE: "xbox"` or `"switch"` and adjust `JOYSTICK_DEVICE` if more than one controller is connected.
4. If pygame sees no device, fix OS/controller permissions before changing policy code.

## Keyboard Focus and Listener Failures

Symptoms:

- Key presses do nothing.
- Movement keys do not change velocity.
- `sshkeyboard` or `pynput` import errors.

Recovery:

- Click/focus the policy terminal, not the MuJoCo viewer, for policy keys.
- Press `=` to enter walking mode before `w/a/s/d`; the code ignores movement keys while `stand_command` is false.
- Install `sshkeyboard` for policy keyboard control and `pynput` for `listener_deltaa.py`.
- If a remote terminal cannot capture keys reliably, use joystick mode after verifying pygame.

## Robot-Type or DOF Mismatch

Symptoms:

- `NotImplementedError: Robot type ... is not supported`
- `ValueError: Invalid robot type ... Expected 'g1', 'h1', or 'go2'.`
- Shape mismatches in command vectors, gains, limits, or ONNX outputs.

Recovery:

- Keep top-level `ROBOT_TYPE: "g1_29dof"` for the supplied G1 deployment config.
- Do not change top-level `ROBOT_TYPE` to `g1_29dof_anneal_23dof`; that name belongs in `mimic_robot_types` and `robot_dofs` masks.
- Confirm all 29-length config lists are still length 29 after edits.
- Confirm the physical G1 has actually been converted/unlocked for the 29-DOF setup before sim2real.

## Policy Path or ONNX Shape Mismatch

Symptoms:

- `FileNotFoundError: Model file not found at ...`
- ONNX Runtime input-shape errors.
- `No mimic models found in the configuration!`

Recovery:

- Use the README height-policy command with the supplied height locomotion checkpoint:

  ```bash
  cd sim2real
  python rl_policy/deepmimic_dec_loco_height.py \
    --config=config/g1_29dof_hist.yaml \
    --loco_model_path=./models/dec_loco/20250109_231507-noDR_rand_history_loco_stand_height_noise-decoupled_locomotion-g1_29dof/model_6600.onnx \
    --mimic_model_paths=./models/mimic
  ```

- Ensure `--mimic_model_paths` contains one subdirectory per key in `mimic_models`, with the configured ONNX filename inside.
- If using a custom exported checkpoint, use the matching config observation history and the matching height/non-height policy script.
- Do not use `--use_jit` with `deepmimic_dec_loco.py`; it raises `NotImplementedError` in the inspected source.

## Wrong Current Working Directory

Symptoms:

- Robot XML or URDF cannot be found.
- `ModuleNotFoundError` for repo-local `rl_policy` or `utils` modules.
- Model path from the README does not exist.

Recovery:

```bash
cd sim2real
python sim_env/base_sim.py --config=config/g1_29dof_hist.yaml
```

If launching from the repository root, rewrite every config/model path and re-check imports; the repo examples are not written that way.

## Real-Data Logger Has Incomplete Samples

Symptoms:

- `Missing low state data for buffer update.`
- `Missing low command data for buffer update.`
- `Missing mocap data for buffer update.`
- Saved `.npz` files have few or no samples.

Recovery:

- Confirm policy or another controller is publishing `rt/lowcmd`.
- Confirm Unitree low state is available on the selected interface/domain.
- Confirm the mocap stack publishes `/odometry` as `nav_msgs/Odometry`.
- Press `;` to start a recording episode and `'` to stop/save; `Ctrl+C` exits without saving an unfinished buffer.

## Hardware Safety Responses

Software controls are not a substitute for a physical emergency stop.

- `o` in the policy terminal disables policy actions in the inspected code.
- `z` zeros commanded velocity but does not disable policy actions.
- `L2` on joystick zeros velocity commands.
- `B+Y` on joystick disables policy actions.
- Keep a human operator ready with the vendor-supported stop/disable method whenever motors are powered.

If behavior is unexpected on hardware, stop immediately, preserve logs/configs, and reproduce in sim2sim before another physical run.
