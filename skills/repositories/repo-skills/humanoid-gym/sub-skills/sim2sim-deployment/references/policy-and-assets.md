# Policy and Asset Contract

## Policy contract

The MuJoCo deployment entry point consumes a **TorchScript** policy via `torch.jit.load(...)`.
It is not a raw training checkpoint loader.
A policy exported by play.py or an equivalent exporter is expected to map the XBot-L observation stack to 12 actions.

### Current shape contract

- Actor input width: `705`
- Actor output width: `12`
- Observation stack: `15` frames × `47` features per frame
- Privileged critic context from the source config: `3` frames × `73` privileged features = `219`

A bundled sample policy exists at `logs/XBot_ppo/exported/policies/policy_example.pt`.
That file is the canonical evidence that a TorchScript policy can be loaded and produces a 12-D action tensor.

## Observation layout

The sim2sim script builds one 47-D frame and stacks 15 frames.
The frame layout is:

| Slice | Size | Meaning |
|---|---:|---|
| `0:2` | 2 | phase `sin` / `cos` |
| `2:5` | 3 | command velocities `vx`, `vy`, `dyaw` after normalization |
| `5:17` | 12 | joint positions for the actuated joints |
| `17:29` | 12 | joint velocities for the actuated joints |
| `29:41` | 12 | previous action |
| `41:44` | 3 | base angular velocity |
| `44:47` | 3 | base Euler angles |

Notes:
- The script slices the last 12 joint positions and velocities from MuJoCo state arrays.
- The final policy input concatenates 15 such frames in time order.
- If you change `frame_stack`, `num_single_obs`, or the feature layout, this sub-skill is no longer a direct fit.

## Control layout

The source sim2sim loop uses these fixed control facts:

| Item | Value | Why it matters |
|---|---:|---|
| MuJoCo timestep | `0.001` s | 1000 Hz physics loop |
| Policy decimation | `10` | policy update at 100 Hz |
| Action scale | `0.25` | policy output is scaled before PD control |
| Torque limit | `200` per joint | torques are clipped |
| PD gains | `kps=[200, 200, 350, 350, 15, 15, 200, 200, 350, 350, 15, 15]` | lower-body position control |
| PD damping | `kds=[10, ... , 10]` | damping matched to the source script |
| Default command velocity | `vx=0.4, vy=0.0, dyaw=0.0` | policy sees fixed command inputs in the source loop |

The source loop computes
`target_q = action * action_scale`,
then applies PD torques and clips them to `tau_limit`.
If your policy was trained with different gains, scale, or command assumptions, expect divergence.

## Asset layout

| Asset | Role |
|---|---|
| `resources/robots/XBot/mjcf/XBot-L.xml` | plane-ground MuJoCo model |
| `resources/robots/XBot/mjcf/XBot-L-terrain.xml` | terrain MuJoCo model |
| `resources/robots/XBot/terrain/uneven.png` | terrain heightfield used by the terrain model |
| `resources/robots/XBot/urdf/XBot-L.urdf` | robot asset reference and joint/body naming source |
| `resources/robots/XBot/meshes/*.STL` | mesh geometry referenced by the robot XML files |

### Actuated joint order

Both MJCF models expose the same 12 actuators in the source order:

1. `left_leg_roll_joint`
2. `left_leg_yaw_joint`
3. `left_leg_pitch_joint`
4. `left_knee_joint`
5. `left_ankle_pitch_joint`
6. `left_ankle_roll_joint`
7. `right_leg_roll_joint`
8. `right_leg_yaw_joint`
9. `right_leg_pitch_joint`
10. `right_knee_joint`
11. `right_ankle_pitch_joint`
12. `right_ankle_roll_joint`

The sim2sim script assumes this ordering when it slices the MuJoCo state and maps the 12 policy outputs back to torques.

## Plane vs terrain

- Plane mode is the default and points to `XBot-L.xml`.
- Terrain mode adds the uneven heightfield and points to `XBot-L-terrain.xml`.
- If the terrain image is missing, the terrain MJCF cannot be used.
- If you only want to confirm policy loading and action shape, plane mode is the lighter first check.

## Config context from XBotLCfg

The current source config also defines:

- `frame_stack = 15`
- `num_single_obs = 47`
- `num_observations = 705`
- `single_num_privileged_obs = 73`
- `c_frame_stack = 3`
- `num_privileged_obs = 219`
- `num_actions = 12`

Those values are the contract this sub-skill is built around.
