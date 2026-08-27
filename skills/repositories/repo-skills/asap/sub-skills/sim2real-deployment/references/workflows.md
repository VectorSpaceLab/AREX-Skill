# ASAP Sim2Sim and Sim2Real Workflows

These workflows distill the deployment paths implemented under the repository `sim2real/` package. They are operational notes for a future agent; they do not make real hardware deployment safe by themselves.

## Shared Setup Checklist

Run deployment commands from the repository `sim2real/` directory:

```bash
cd sim2real
```

Install the repo and deployment helper package in the intended runtime environment:

```bash
pip install -e ..
pip install -e .
```

Install external pieces that the repo imports but does not vendor:

```bash
# ROS2 Python via robostack, matching the README's Humble route
conda config --env --add channels conda-forge
conda config --env --add channels robostack-staging
conda config --env --remove channels defaults || true
conda install ros-humble-desktop

# Unitree SDK2 Python; use the official source appropriate for the lab/network
# README shows SSH, but HTTPS may be easier on machines without GitHub SSH keys.
git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
cd unitree_sdk2_python
pip install -e .
pip install --upgrade numpy scipy

# Deployment-side runtime packages imported by sim2real code paths
pip install pygame sshkeyboard pynput termcolor
```

Check ROS2 after installation:

```bash
rviz2
```

A minimal safe static check, without DDS initialization or motor commands, is:

```bash
python sub-skills/sim2real-deployment/scripts/deployment_doctor.py \
  --repo-root <asap-checkout> \
  --mode sim2sim \
  --config sim2real/config/g1_29dof_hist.yaml \
  --loco-model-path sim2real/models/dec_loco/20250109_231507-noDR_rand_history_loco_stand_height_noise-decoupled_locomotion-g1_29dof/model_6600.onnx \
  --mimic-model-paths sim2real/models/mimic
```

If the skill has been imported outside the checkout, run the same script from the imported skill location and keep `--repo-root` pointed at the ASAP checkout.

## Sim2Sim MuJoCo Playback

Sim2Sim runs the MuJoCo simulator as a fake Unitree low-level DDS endpoint, then runs the same policy script against that simulated low state/low command stream. Even though no robot is connected, `rclpy` and `unitree_sdk2py` are still required because `sim_env/base_sim.py` imports both and builds the bridge.

1. Keep the deployment config local to the machine:

   ```yaml
   # sim2real/config/g1_29dof_hist.yaml
   INTERFACE: "lo"     # Linux localhost; use "lo0" on macOS if needed
   DOMAIN_ID: 0
   USE_JOYSTICK: 0     # set to 1 only after pygame sees the controller
   ```

2. Terminal A — start MuJoCo simulator from `sim2real/`:

   ```bash
   cd sim2real
   python sim_env/base_sim.py --config=config/g1_29dof_hist.yaml
   ```

3. Terminal B — start the decoupled locomotion + mimic policy:

   ```bash
   cd sim2real
   python rl_policy/deepmimic_dec_loco_height.py \
     --config=config/g1_29dof_hist.yaml \
     --loco_model_path=./models/dec_loco/20250109_231507-noDR_rand_history_loco_stand_height_noise-decoupled_locomotion-g1_29dof/model_6600.onnx \
     --mimic_model_paths=./models/mimic
   ```

4. Bring-up sequence:
   - Wait until the simulator viewer is open and the policy no longer reports missing low state.
   - In the MuJoCo viewer, press `9` to toggle the elastic band/release support when ready. Keys `7` and `8` adjust the elastic-band length.
   - In the policy terminal, press `i` to interpolate toward the initial/default pose.
   - Press `]` to allow locomotion policy actions.
   - Press `=` to toggle walking/standing before using velocity keys; movement keys are ignored while the stand command is false.
   - Use `w/a/s/d`, `q/e`, and `z` for velocity commands.
   - Press `[` to toggle the ASAP/mimic policy; use `;` and `'` to choose the next/previous mimic checkpoint while in locomotion mode.
   - Press `o` to disable policy actions and send zero/hold commands.

## Sim2Real Unitree G1 Runtime

Only run this workflow with qualified hardware supervision. `deepmimic_dec_loco_height.py` publishes `rt/lowcmd` and consumes `rt/lowstate`; incorrect gains, wrong robot type, wrong interface, or wrong DOF setup can be dangerous.

1. Prepare the robot before starting the policy:
   - Configure the Unitree G1 for 29 DOF following the vendor waist-unlock/waist-fastener documentation and restart the robot after the mechanical change.
   - Enter G1 low-level mode with the README sequence: wait for steady blue head light, press `L2+R2`, then `L2+A`, then `L2+B` on the Unitree controller.
   - Connect the control PC to the G1 over Ethernet using the Unitree quick-development network setup.
   - Confirm the PC interface has an address in the Unitree subnet, commonly `192.168.123.xxx`.

2. Edit `sim2real/config/g1_29dof_hist.yaml` for the real network interface:

   ```yaml
   INTERFACE: "eth0"   # replace with the interface that owns 192.168.123.xxx
   DOMAIN_ID: 0
   USE_JOYSTICK: 0     # or 1 after joystick testing
   ROBOT_TYPE: "g1_29dof"
   ```

3. Run the safe doctor in real mode before policy startup:

   ```bash
   python sub-skills/sim2real-deployment/scripts/deployment_doctor.py \
     --repo-root <asap-checkout> \
     --mode sim2real \
     --config sim2real/config/g1_29dof_hist.yaml \
     --loco-model-path sim2real/models/dec_loco/20250109_231507-noDR_rand_history_loco_stand_height_noise-decoupled_locomotion-g1_29dof/model_6600.onnx \
     --mimic-model-paths sim2real/models/mimic
   ```

4. Start the policy from `sim2real/` only after the hardware checklist is complete:

   ```bash
   cd sim2real
   python rl_policy/deepmimic_dec_loco_height.py \
     --config=config/g1_29dof_hist.yaml \
     --loco_model_path=./models/dec_loco/20250109_231507-noDR_rand_history_loco_stand_height_noise-decoupled_locomotion-g1_29dof/model_6600.onnx \
     --mimic_model_paths=./models/mimic
   ```

5. Start conservatively:
   - Press `i` first to move toward the default pose.
   - Press `]` only when the human operator is ready to allow policy actions.
   - Use small velocity increments; each `w/s/a/d/q/e` press changes a command by `0.1`.
   - Keep `o` available to disable policy actions. Treat it as a software stop, not as a replacement for physical emergency stop.

## ROS2 State Publisher

`state_publisher.py` publishes Unitree low state into ROS2 as `std_msgs/Float64MultiArray` on `robot_state`. It is useful when another ROS2 tool needs state, but it still initializes Unitree DDS and requires the same `INTERFACE`/`DOMAIN_ID` setup.

```bash
cd sim2real
python state_publisher.py --config=config/g1_29dof_hist.yaml
```

The script publishes at `1000 Hz` by default and waits until a low-state message arrives. If it prints `Waiting for low state`, check DDS setup, low-level mode, and interface selection before changing code.

## Real-Data Collection with `listener_deltaa.py`

`rl_policy/listener_deltaa.py` logs synchronized Unitree low state, low command, and motion-capture odometry for delta-action experiments. It requires:

- `unitree_sdk2py` DDS low-state and low-command channels.
- ROS2 `rclpy` and a `/odometry` topic (`nav_msgs/Odometry`) from the lab's mocap stack.
- `pynput` for keyboard start/stop keys.

Run from `sim2real/`:

```bash
cd sim2real
python rl_policy/listener_deltaa.py --config=config/g1_29dof_hist.yaml --exp_name my_real_trial
```

Recording keys:

| Key | Effect |
| --- | --- |
| `;` | Start recording a new episode, clear the buffer, and keep appending synchronized samples. |
| `'` | Stop recording, save `motion_<episode>.npz`, clear the buffer, and increment the episode counter. |
| `Ctrl+C` | Exit and print the save directory; the script's signal handler does not automatically save an unfinished buffer. |

Default output, when run from `sim2real/`, is under:

```text
../humanoidverse/logs/delta_a_realdata/<exp_name>/<timestamp>/motion_<n>.npz
```

Saved arrays include time, joint positions/velocities/torques, IMU quaternion/gyro/acceleration, commanded q/dq/kp/kd/tau, mocap position/quaternion, and mocap linear/angular velocity.

## Control Maps

### Keyboard controls implemented by `BasePolicy`

| Key | Implemented effect |
| --- | --- |
| `]` | Enable policy actions and reset the policy phase to `0.0`. |
| `o` | Disable policy actions and leave the robot in hold/zero-action mode. |
| `i` | Enter get-ready interpolation toward default DOF angles for up to 500 policy ticks. |
| `=` | Toggle stand/walk command; when toggled off, zero linear and angular velocity commands. |
| `w` / `s` | Increase/decrease forward linear velocity by `0.1`, only while walk command is active. |
| `a` / `d` | Increase/decrease lateral velocity by `0.1`, only while walk command is active. |
| `q` / `e` | Decrease/increase yaw angular velocity by `0.1`. |
| `z` | Zero linear and angular velocity commands. |
| `1` / `2` | Increase/decrease base-height command by `0.05`. |
| `4` / `7` | Decrease/increase all motor `kp` by a coarse `0.1` scale step. Hardware experts only. |
| `5` / `6` | Decrease/increase all motor `kp` by a fine `0.01` scale step. Hardware experts only. |
| `0` | Reset `kp` scale to `1.0`. |

### Additional keyboard controls in `MotionTrackingDecLocoPolicy`

| Key | Implemented effect |
| --- | --- |
| `[` | Toggle locomotion versus ASAP mimic policy. Entering mimic starts interpolation to that motion's configured upper-body start pose; leaving mimic interpolates back to locomotion. |
| `;` | Select next mimic policy, only while currently in locomotion mode. |
| `'` | Select previous mimic policy, only while currently in locomotion mode. |

### Joystick controls handled by `BasePolicy` and `MotionTrackingDecLocoPolicy`

Enable with `USE_JOYSTICK: 1` and set `JOYSTICK_TYPE: "xbox"` or `"switch"` in `g1_29dof_hist.yaml`. The simulator bridge publishes a Unitree-style wireless-controller message from `pygame`; the policy subscribes to `rt/wirelesscontroller`.

| Button/input | Implemented effect |
| --- | --- |
| Left stick | Linear velocity command, scaled by `0.5`, active only while walk command is true. |
| Right stick X | Yaw command, active only while walk command is true. |
| `start` | Reset history, enable policy actions, reset phase. |
| `B+Y` | Disable policy actions. |
| `A+X` | Enter get-ready/default-pose interpolation. |
| `R2` | Toggle stance/walk; when entering walk, reset base height to `0.78`. |
| `L2` | Zero linear and angular velocity commands. |
| `B+up` / `B+down` | Increase/decrease base-height command by `0.05` while not walking. |
| `Y+left` / `Y+right` | Coarse `kp` scale decrease/increase by `0.1`. Hardware experts only. |
| `A+left` / `A+right` | Fine `kp` scale decrease/increase by `0.01`. Hardware experts only. |
| `A+Y` | Reset `kp` scale to `1.0`. |
| `select` | Toggle locomotion versus mimic policy and reset history. |
| `R1` / `L1` | Select next/previous mimic policy. |

### MuJoCo viewer keys from `ElasticBand`

| Viewer key | Effect |
| --- | --- |
| `7` | Shorten elastic-band support length by `0.1`. |
| `8` | Lengthen elastic-band support length by `0.1`. |
| `9` | Toggle elastic-band force on/off. README uses this to release support after startup. |
