# Robots, Grippers, and Bases

This reference covers the registries used by controller configs, how `create_composite_robot` rewires them, and the common built-in robot/base/gripper combinations.

## 1) Registry snapshots

Public registries are exposed through the package-level helpers.

### Robots

Verified environment-facing robot names include:

`Baxter`, `GR1`, `GR1ArmsOnly`, `GR1FixedLowerBody`, `GR1FloatingBody`, `IIWA`, `Jaco`, `Kinova3`, `Panda`, `PandaDexLH`, `PandaDexRH`, `PandaOmron`, `Sawyer`, `SpotArm`, `SpotWithArm`, `SpotWithArmFloating`, `Tiago`, `UR5e`, `XArm7`.

### Grippers

Verified gripper names include:

`BDGripper`, `FourierLeftHand`, `FourierRightHand`, `InspireLeftHand`, `InspireRightHand`, `JacoThreeFingerDexterousGripper`, `JacoThreeFingerGripper`, `PandaGripper`, `RethinkGripper`, `Robotiq140Gripper`, `Robotiq85Gripper`, `RobotiqThreeFingerDexterousGripper`, `RobotiqThreeFingerGripper`, `SuctionGripper`, `WipingGripper`, `XArm7Gripper`, and `None` for `NullGripper`.

### Bases

Verified base names include:

`FloatingLeggedBase`, `NoActuationBase`, `NullBase`, `NullMobileBase`, `NullMount`, `OmronMobileBase`, `RethinkMinimalMount`, `RethinkMount`, `Spot`, `SpotFloating`.

## 2) How composite robot creation works

Use `create_composite_robot(name, robot, base=None, grippers=None)` to make a new robot class in-process.

```python
from robosuite.utils.robot_composition_utils import create_composite_robot

create_composite_robot(
    name="CustomPanda",
    robot="Panda",
    base="RethinkMount",
    grippers="PandaGripper",
)
```

Rules worth remembering:

- If `base=None`, the helper uses the source robot's default base.
- If the source robot is bimanual and you provide one gripper, the helper duplicates it for both arms.
- If the source robot is single-arm and you provide two grippers, the helper warns and keeps the first one.
- `Tiago` and `GR1` ignore a custom `base` and force their own mobile / legged base choice.
- The helper registers the new class only in the current Python process.
- `FloatingLeggedBase` is present in the base registry, but it is not a general target in `create_composite_robot`'s base mapping.

Base family to robot-class mapping used by the helper:

| Base | Target robot class |
| --- | --- |
| `RethinkMount`, `RethinkMinimalMount`, `NullMount` | `FixedBaseRobot` |
| `OmronMobileBase`, `NullMobileBase` | `WheeledRobot` |
| `NoActuationBase`, `Spot`, `SpotFloating` | `LeggedRobot` |

## 3) Common built-in robot combinations

The current package snapshot includes robot-specific controller presets for the following families:

| Robot | Default base | Default gripper(s) | Preset controller file |
| --- | --- | --- | --- |
| `Panda` | `RethinkMount` | `PandaGripper` | `default_panda.json` |
| `Sawyer` | `RethinkMount` | `RethinkGripper` | `default_sawyer.json` |
| `IIWA` | `RethinkMount` | `Robotiq140Gripper` | `default_iiwa.json` |
| `Kinova3` | `RethinkMount` | `Robotiq85Gripper` | `default_kinova3.json` |
| `UR5e` | `RethinkMount` | `Robotiq85Gripper` | `default_ur5e.json` |
| `Baxter` | `RethinkMinimalMount` | `RethinkGripper` on both arms | `default_baxter.json` |
| `PandaOmron` | `OmronMobileBase` | `PandaGripper` | `default_pandaomron.json` |
| `Tiago` | `NullMobileBase` | `Robotiq85Gripper` on both arms | `default_tiago.json` |
| `GR1` / `GR1FixedLowerBody` / `GR1FloatingBody` | `NoActuationBase` or `FloatingLeggedBase` depending on variant | `FourierRightHand` / `FourierLeftHand` | `default_gr1*.json` |
| `SpotWithArm` | `Spot` | `BDGripper` | `default_spotwitharm.json` |
| `PandaDexRH` | `RethinkMount` | `InspireRightHand` | `default_panda_dex.json` |
| `PandaDexLH` | `RethinkMount` | `InspireLeftHand` | `default_panda_dex.json` |

Fallback note:

- Some registered robots in this snapshot, such as `Jaco`, `SpotArm`, `SpotWithArmFloating`, and `XArm7`, do not have a matching `controllers/config/robots/default_<name>.json` file. `load_composite_controller_config(robot=...)` falls back to `BASIC` for those names.

## 4) Choosing a robot / gripper / base

Practical rules:

- Use a fixed-base robot for arm-only manipulation tasks.
- Use `PandaOmron` or `Tiago` when you need a wheeled mobile base.
- Use `GR1*` or `SpotWithArm*` when you want a legged / humanoid body part layout.
- Use `PandaDexRH` / `PandaDexLH` for dexterous hand experiments.
- Treat `robosuite_models` as optional: extra robots, grippers, and bases may appear if that package is installed, but the current verification did not include it.

## 5) Cross-checks

After composing a custom robot, verify the resulting body-part names before tuning controllers:

- `../modeling` for robot XML structure and mounting checks
- `scripts/print_action_info.py` for action split inspection
- `scripts/validate_controller_config.py` for config-shape checks
