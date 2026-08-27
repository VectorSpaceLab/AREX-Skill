# MyoSuite task catalog

Import `myosuite` before reading this catalog. Registration is performed as an
import side effect, so an unimported registry is not evidence that a task is
absent. The authoritative runtime view is:

```python
import myosuite
from myosuite.utils import gym

print("MyoBase:", myosuite.myosuite_myobase_suite)
print("MyoChallenge:", myosuite.myosuite_myochal_suite)
print("MyoDM:", myosuite.myosuite_myodm_suite)
print("All:", myosuite.myosuite_env_suite)
```

Use `gym.spec(id)` and then `gym.make(id)`; do not infer availability only from
a prose catalog. IDs are versioned with a `-v0` or `-v1` suffix.

## MyoBase families

These are the core registered task families and their concrete base IDs in the
inspected release.

| Family | Concrete IDs | Purpose |
|---|---|---|
| Motor finger reach | `motorFingerReachFixed-v0`, `motorFingerReachRandom-v0` | Torque-actuated finger tip reach |
| Myo finger reach | `myoFingerReachFixed-v0`, `myoFingerReachRandom-v0` | Muscle-actuated finger tip reach |
| Elbow pose | `myoElbowPose1D6MFixed-v0`, `myoElbowPose1D6MRandom-v0` | Six-muscle elbow pose control |
| Elbow exosuit pose | `myoElbowPose1D6MExoFixed-v0`, `myoElbowPose1D6MExoRandom-v0` | Elbow pose with exosuit actuator |
| Motor finger pose | `motorFingerPoseFixed-v0`, `motorFingerPoseRandom-v0` | Torque-actuated finger joint pose |
| Myo finger pose | `myoFingerPoseFixed-v0`, `myoFingerPoseRandom-v0` | Muscle-actuated finger joint pose |
| Hand pose | `myoHandPoseFixed-v0`, `myoHandPoseRandom-v0` | Coordinated hand joint pose |
| Hand reach | `myoHandReachFixed-v0`, `myoHandReachRandom-v0` | Multi-tip hand reaching |
| Key turn | `myoHandKeyTurnFixed-v0`, `myoHandKeyTurnRandom-v0` | Thumb/index key rotation |
| Object hold | `myoHandObjHoldFixed-v0`, `myoHandObjHoldRandom-v0` | Move and stabilize an object |
| Pen twirl | `myoHandPenTwirlFixed-v0`, `myoHandPenTwirlRandom-v0` | Rotate a pen without dropping it |
| Torso pose | `myoTorsoPoseFixed-v0`, `myoTorsoExoPoseFixed-v0` | Lumbar/torso pose control |
| Leg standing/walking | `myoLegStandRandom-v0`, `myoLegWalk-v0` | Stand or walk on flat ground |
| Leg terrain walking | `myoLegRoughTerrainWalk-v0`, `myoLegHillyTerrainWalk-v0`, `myoLegStairTerrainWalk-v0` | Terrain locomotion |
| Hand reorientation | `myoHandReorient8-v0`, `myoHandReorient100-v0`, `myoHandReorientID-v0`, `myoHandReorientOOD-v0` | Parameterized object reorientation |

The hand-pose registration also creates `myoHandPose0Fixed-v0` through
`myoHandPose9Fixed-v0` for the ten fixed ASL-style poses. Confirm these IDs at
runtime because generated catalogs can vary with package version.

## Automatic condition variants

`myo`-prefixed MyoBase registrations create condition variants by inserting the
condition token after the `myo` prefix:

- `myoSarc...`: sarcopenia, reducing muscle gain/force in the task;
- `myoFati...`: cumulative fatigue model;
- `myoReaf...`: hand-only tendon-transfer/reafferentation variants where
  registered.

Examples include `myoSarcElbowPose1D6MRandom-v0`,
`myoFatiElbowPose1D6MRandom-v0`, and hand `myoReafHand...` variants. Motor-
finger IDs do not receive these `myo`-prefix variants. Prefer runtime listing
over manually constructing a variant name.

## Other registered suites

The combined registry also includes separate suites. They are not required for
a core lifecycle smoke and often need larger model/data assets:

- **MyoChallenge**: die reorientation, Baoding balls, relocate, chase-tag,
  OSL run-track, soccer, table tennis, and bimanual tasks. Representative IDs
  include `myoChallengeDieReorientP1-v0`,
  `myoChallengeBaodingP1-v1`, `myoChallengeRelocateP1-v0`,
  `myoChallengeChaseTagP1-v0`, `myoChallengeOslRunFixed-v0`,
  `myoChallengeSoccerP1-v0`, and `myoChallengeTableTennisP1-v0`.
- **MyoDM**: reference-tracking object tasks, including `MyoHand...-v0`
  tracking IDs and generated fixed/random object IDs. These tasks belong to
  reference playback and should be routed there for trajectory semantics.
- **MyoEdits**: edited-arm reach tasks `myoArmReachFixed-v0` and
  `myoArmReachRandom-v0`; their model-editing behavior belongs to the
  model-editing route even though creation uses the same Gymnasium API.

Challenge and DM IDs can be enumerated without creating them:

```python
for task_id in myosuite.myosuite_env_suite:
    if task_id.startswith("myoChallenge"):
        print(task_id)
```

Do not use a challenge or DM task as the first installation smoke: choose
`myoElbowPose1D6MRandom-v0` or another small MyoBase pose/reach task first.

## Selection heuristics

- Use a `Fixed` ID to remove target randomization when checking API wiring.
- Use a `Random` ID to exercise seeded target/reset behavior.
- Use the elbow pose task for a low-cost base smoke; it has a bounded 100-step
  registration and was the verified reset/step candidate.
- Use hand/leg/terrain tasks only after the base route works; their models have
  larger actuator/asset footprints.
- Treat the registration's `max_episode_steps` as the wrapper limit, not as a
  promise that a random policy will solve the task.
