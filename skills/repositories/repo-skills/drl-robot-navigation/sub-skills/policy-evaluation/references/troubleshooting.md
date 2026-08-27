# Policy-evaluation troubleshooting

Use the artifact checker before investigating simulator behavior. Keep artifact failures,
environment blocks, and policy outcomes as separate categories.

## `missing_actor` or critic-only directory

**Signal:** `<base>_critic.pth` exists but `<base>_actor.pth` does not, or the actor
name differs from the requested base.

**Action:** stop. A critic estimates values and cannot emit the two control actions.
Confirm the requested base name and model directory from the run record. Do not copy,
rename, or substitute a critic. If the actor was never saved, recover it from the
training artifact source or choose another complete run outside this skill.

## `actor_ready_critic_missing`

**Signal:** the actor is present and inventory-compatible, but no critic companion exists.

**Action:** actor-only evaluation is structurally allowed, but label the artifact set
incomplete. Use `--require-critic` only if a caller has its own strict pair gate; the
bundled checker reports the absence without making actor-only evaluation depend on it.
Do not claim this is a complete TD3 checkpoint.

## `incompatible_actor` or wrong dimensions

**Signal:** safe loading reports missing/unexpected keys, non-tensor values, or a shape
such as `[799, 24]` where `[800, 24]` is required.

**Action:** stop before ROS. Check that the run used state width 24, action width 2, and
the 800/600 actor widths. A `module.` prefix, an actor from another environment, a
checkpoint containing a whole module, or a different policy architecture needs an
explicit conversion/skill outside this sub-skill. Never bypass the shape gate by calling
`load_state_dict(strict=False)`.

## Safe loader unavailable or rejected

**Signal:** the optional check says PyTorch is unavailable, `torch.load` has no
`weights_only` argument, the file exceeds the byte limit, or safe loading fails.

**Action:** treat compatibility as unverified. Do not fall back to unrestricted
`torch.load`, `pickle`, or whole-module deserialization. Run the default inventory to
separate naming/presence facts from loader availability, then arrange a reviewed
inspection environment or regenerate the artifact in a supported state-dict format.

## Corrupt, non-regular, or symlink artifact

**Signal:** status is `rejected_symlink`, `rejected_not_regular_file`, `stat_error`, or
`rejected_too_large`.

**Action:** do not load it. Obtain a regular, size-bounded artifact through the approved
artifact-transfer process and rerun the checker. A symlink may point somewhere outside
the intended model directory and is not accepted by the helper.

## Import starts ROS/Gazebo or hangs

**Signal:** a smoke test tries to import the reference evaluator and launches processes,
waits for ROS, or never returns.

**Action:** stop the process safely. The reference environment is constructed at module
import time, and the test loop is intentionally unbounded. Do not use import as a
checkpoint test. Use the bundled artifact checker for a dry run and use a controlled
runner with explicit episode/step and wall-clock limits for simulator evaluation.

## ROS/Gazebo readiness failure

**Signal:** missing `roscore`, `roslaunch`, Gazebo, ROS Python message modules, the
navigation launch asset, or reset/pause/unpause/topics.

**Action:** report **environment blocked**, not a bad policy and not a zero score. The
setup owner must prepare the approved ROS Noetic/Gazebo runtime. This sub-skill does not
install or repair that stack. Do not claim simulator verification on a host where those
components are absent.

## State length or non-finite value

**Signal:** reset/step returns a state other than 24 values, or NaN/Inf appears in state
or actor output.

**Action:** abort the episode, record the invalid transition, and investigate sensor,
odometry, reset, or checkpoint compatibility. Do not reshape, pad, truncate, or replace
sensor values silently. A state-contract failure invalidates the episode.

## Action range or conversion error

**Signal:** actor output is not finite or not two normalized values in `[-1, 1]`, or the
runner sends the normalized first action directly as linear velocity.

**Action:** abort. The actor output is normalized; only the first component is converted
to `(a0 + 1) / 2`, while the second remains angular velocity. Do not add training
exploration noise to an evaluation run.

## Run never ends

**Signal:** evaluation continues after the requested episodes or remains active after
500 steps.

**Action:** invoke the external watchdog/operator stop, retain partial metrics, and mark
the run incomplete. Every controlled run needs an episode count, 500-step per-episode
cap, wall-clock deadline, and cleanup plan. Never rely on the simulator's `done` flag
alone.

## Low reward, collision, or no goal

**Signal:** the artifact and simulator gates pass, but navigation metrics are poor.

**Action:** report the bounded per-episode metrics and termination mix without changing
the checkpoint or claiming reproduction. Compare only runs with the same environment,
seed policy, action conversion, and bounds. A successful load proves compatibility, not
behavioral quality.
