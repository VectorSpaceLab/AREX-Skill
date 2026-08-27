# Optional integrations matrix

A successful `import smarts` or `scl --help` validates the core package only.
Use this matrix to decide whether an integration is available, which boundary
owns it, and what evidence is still required.

| Integration | Package/data/system boundary | Extra or probe | Availability in prepared environment | Safe interpretation |
|---|---|---|---|---|
| SUMO and TraCI | External SUMO binaries, `sumolib`, `traci`, map XML, and a free TCP port | `sumo`; probe `sumo`, `sumo-gui`, `sumo.tools.traci` or `sumolib` | Not installed | Core CLI help remains valid. A SUMO-backed scenario cannot be claimed runnable; see [sumo-traci.md](sumo-traci.md). |
| OpenDRIVE | `.xodr` map input converted through OpenDRIVE support and spatial indexing | `opendrive`; probe `opendrive2lanelet` | Import passed | Import is not validation of a user's road network, coordinate system, or scenario metadata. |
| Waymo | Waymo Scenario-proto TFRecord data, protobuf compatibility, plotting, and output directory | `waymo`; probe `smarts.waymo`, protobuf, and any external dataset package | No external Waymo stack or downloaded data | SMARTS's bundled Waymo code may import, but no dataset operation is verified. The CLI expects Scenario-proto format, not `tf.Example`; `overview` is the read-only first action. |
| Argoverse 2 | `av2` plus Rtree and a scenario directory containing map archive JSON and scenario parquet | `argoverse`; probe `av2` | Not installed | No Argoverse map/replay claim. Install the scoped extra and provide a valid local dataset only when needed. |
| ROS | ROS installation, message/runtime packages, and usually a running ROS master/nodes; Python helpers are not the whole system | `ros`; probe `rospkg`, `catkin_pkg`, and system commands separately | Not installed | `rospkg` availability would not prove ROS graph/service availability. No ROS command is in the verified `scl` tree. |
| Envision | SMARTS Envision server/client, websocket endpoint, browser/display, JSONL records | `envision`; probe `envision` | Import passed | Server startup and replay are workflow operations; they require a free port and valid records. API/data details belong to sensors-visualization. |
| Panda3D/software rendering | Panda3D, optional camera dependencies, and X11/Xvfb/display support | `camera-obs`; probe `panda3d.core` | Import/offscreen smoke passed | Full renderer, camera timing, and display behavior remain unverified. |
| Ray/RLlib | Ray, RLlib, policy/config compatibility, and often Torch/TensorFlow | `ray`, `rllib`, plus chosen training backend | Ray/RLlib/Torch/TensorFlow not installed | Do not run zoo/RL workflows or claim training support from core CLI help. Route implementation to rl-agent-zoo. |
| Visdom | Visdom Python client and a separately running server | `visdom`; probe import and configured endpoint | Not installed | Disabled/absent Visdom is unrelated to core CLI health. |

## Data contracts

- **Waymo:** point the CLI at a downloaded Scenario-proto TFRecord. Use
  `scl waymo overview FILE` to enumerate IDs, then `preview FILE ID` or
  `export FILE ID OUTPUT_DIR`. Expect protobuf version issues to show up at
  import/parse time; do not regenerate generated files automatically.
- **Argoverse:** a scenario directory needs the scenario parquet and matching
  map archive JSON. A package import without those files cannot build a map.
- **OpenDRIVE:** provide the map source expected by the selected scenario and
  keep generated lane/map output separate from source data. Check `scl` and
  scenario-studio boundaries before changing a map.
- **SUMO:** a `.net.xml`/traffic source may cause SMARTS to import the SUMO
  provider lazily. A base import therefore does not exercise SUMO.
- **ROS:** distinguish Python import, a local ROS installation, a live master,
  and application message compatibility. Test each explicitly and read-only
  before attempting a simulation.

## Optional dependency procedure

1. Run `python scripts/check_optional_integrations.py` from any cwd.
2. For an explicitly required integration, install only its documented extra in
   a new/isolated environment; never let the checker install it.
3. Probe the executable and package in the same environment as `scl`.
4. Validate a tiny local data fixture or use the integration's own read-only
   listing/help command.
5. Record unavailable data/services as an explicit gap. Do not downgrade a core
   CLI failure into an optional failure without checking the traceback's import
   boundary.

The prepared environment has no external SUMO/ROS/Waymo/Argoverse/RL stacks.
That absence is intentional and must remain visible in handoffs.
