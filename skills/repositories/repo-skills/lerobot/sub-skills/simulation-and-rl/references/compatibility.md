# Compatibility, installation, and backend gates

LeRobot release facts: package version **0.6.2**, Python `>=3.12`, core
NumPy `>=2.0,<2.3`, Gymnasium `>=1.1.1,<2`, Torch `>=2.7,<2.12`, and
OpenCV-headless `>=4.9,<4.14`. These are the base constraints in the release
metadata. Optional benchmark packages may deliberately require a separate
environment.

## LeRobot extras

Install only the requested extra, not `all`, when investigating a benchmark.
The release exposes these simulation/RL extras:

| Extra | Important contents | Gate |
|---|---|---|
| `pusht` | `gym-pusht`, Pymunk, dataset/video support | CPU-friendly simulation package |
| `aloha` | `gym-aloha`, SciPy, dataset/video support | task package and camera backend |
| `libero` | Linux `hf-libero`, SciPy, Transformers, dataset/video support | Linux, MuJoCo, task assets, render backend |
| `metaworld` | MetaWorld `3.0.0`, SciPy, dataset/video support | MetaWorld/Gymnasium compatibility |
| `hilserl` | `gym-hil`, gRPC/protobuf, Transformers, dataset, placo | simulator or hardware, input device, service topology |
| `kinematics` | placo plus pinned cmeel ABI packages | Linux binary ABI; required by some HIL paths |
| `evaluation` | video backend | policy and environment extras remain separate |
| `all` | broad composite selection | not recommended for conflict diagnosis |

Policy extras (for example `smolvla`, `pi`, or other model-specific groups)
are separate from environment extras. A successful policy import does not
mean a simulator is installed.

## Explicitly absent extras

The following names are intentionally **not** pyproject extras in this
release:

- **VLABench**: distributed as an external source package and needs its RRT
  dependency, MuJoCo/dm-control compatibility, and mesh assets.
- **RoboCasa**: upstream setup metadata pins an old LeRobot version, so the
  integration expects manually managed editable packages and `--no-deps`-style
  isolation from that shadowed pin.
- **RoboMME**: its ManiSkill dependency pins `gymnasium==0.29.1` and
  `numpy<2`, conflicting with the base release's NumPy/Gymnasium constraints.
  Use a separate Linux environment or the maintained benchmark container.
- **RoboTwin/RobotWin**: the simulator tree, assets, SAPIEN, CuRobo, mplib,
  and PyTorch3D are external; there is no compact LeRobot extra that proves
  the full stack.
- **LIBERO-plus**: install the plus fork and asset pack separately. It
  replaces vanilla LIBERO's import namespace; both variants cannot safely
  coexist in one Python environment.
- **IsaacLab Arena**: it is a Hub-hosted environment route, not a local
  package extra. It adds remote code and an Isaac/Omniverse runtime gate.

Do not “fix” an absent extra by inventing a package name or installing an
unbounded replacement. Stop with a package-specific diagnosis.

## Known conflicts and repairs

### MetaWorld/Gymnasium mismatch

MetaWorld `3.0.0` can fail with an assertion showing render modes such as
`['human', 'rgb_array', 'depth_array']` when paired with an incompatible
Gymnasium release. The repository documentation identifies
`gymnasium==1.1.0` as the repair. This is below the current core floor, so
repairing it may require an isolated environment and a deliberate compatibility
review; do not silently downgrade a shared LeRobot environment. A config probe
cannot detect the runtime render assertion without importing and constructing
the simulator.

### RoboMME NumPy/Gymnasium conflict

ManiSkill/SAPIEN in RoboMME has a NumPy 1.x and Gymnasium 0.29.x expectation.
The core release has NumPy 2.x and Gymnasium 1.1.x. If installation reports
that resolver conflict, stop and recommend the isolated benchmark environment.
Do not force a mixed process and then report a successful LeRobot benchmark.
The wrapper may import under mocks while the real SAPIEN renderer remains
unavailable.

### RoboCasa shadowed LeRobot pin

RoboCasa's setup metadata historically declares `lerobot==0.3.3`. Installing
it normally can replace or conflict with the intended 0.6.2 workspace. Keep
RoboCasa and robosuite externally managed and verify `import lerobot` still
resolves to the expected release before any run. The wrapper default restricts
object registries to `lightwheel`; requesting an absent `objaverse` pack can
produce an upstream zero-probability/NaN sampling crash.

### Placo and cmeel ABI

The `placo` dependency is capped below the ABI-breaking release and is paired
with cmeel urdfdom/tinyxml2 bounds. If `import placo` fails with a missing
`liburdfdom_sensor` or `libtinyxml2` soname, classify it as a kinematics binary
ABI issue and repair the isolated environment; do not classify it as an RL
algorithm error.

## Backend matrix

| Backend | What it proves | What it does not prove |
|---|---|---|
| CPU + no display | static config, registry, and some state-only unit behavior | EGL/Vulkan camera rendering, GPU policies, simulator throughput |
| CPU + MuJoCo software/offscreen | possibly a bounded image reset | production reproducibility or GPU renderer behavior |
| CUDA | tensor/policy acceleration and some GPU simulators | Vulkan/EGL driver interop or asset correctness |
| EGL (`MUJOCO_GL=egl`) | requested MuJoCo headless context can be attempted | that the driver, assets, or task is stable |
| Vulkan | SAPIEN/ManiSkill rendering can be attempted | CUDA memory, task success, or all episodes |
| NVIDIA Isaac stack | required IsaacLab backend may run | permission/trust of Hub remote code, which remains explicit |
| gamepad/keyboard | human input can be attached | physical safety or robot connection authorization |

The environment may create GPU/EGL resources lazily in a worker. Always run
one synchronous task first. Async vector workers can expose stale renderer
contexts, process-start-method problems, or per-worker asset failures that a
config check cannot see.

## Credential and code gates

- Local benchmarks need no Hub credential unless the policy/checkpoint or
  dataset is remote.
- Hub policy/reward/dataset loading may require a token, network, cache, and a
  pinned revision; record all of them.
- IsaacLab Arena's `trust_remote_code` must be `true` only with explicit user
  consent because the factory imports and executes a Hub-provided Python
  module. A public repository ID is not consent.
- VLM reward models such as Robometer/TOPReward may load model code or weights
  from the Hub. A config construction is safe; model construction has a
  network/credential/VRAM gate.

## Substitution policy

A CPU config or synthetic RL smoke can substitute for a missing GPU rollout
only as a **partial/none** result. It can verify registry wiring, field
validation, transition schemas, algorithm construction, or reward processor
shapes. It cannot verify benchmark physics, visual success, render stability,
asset coverage, action grounding, or published metrics. State this explicitly
in every handoff.
