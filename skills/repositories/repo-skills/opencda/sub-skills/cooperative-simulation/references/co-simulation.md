# CARLA-SUMO co-simulation

## Required components

`CoScenarioManager` extends the normal OpenCDA scenario manager. It needs a
reachable CARLA server and map, a compatible CARLA Python client (the inspected
client import was 0.9.12), SUMO with its Python tools and TraCI, `SUMO_HOME`, a
valid SUMO configuration directory, and scenario YAML values under `sumo` for
`host`, `port`, `gui`, `client_order`, and `step_length`. The configured step
length should match the CARLA synchronous step. `sumolib`, `traci`, the SUMO
binary, and the network/route assets are separate prerequisites; OpenCDA core
imports do not prove any of them.

The co-simulation directory convention is significant. If
`sumo_file_parent_path` points to a directory named `MapName`, initialization
expects `MapName/MapName.sumocfg`. That configuration normally references
`MapName.net.xml` and `MapName.rou.xml` (or explicit equivalent relative files).
Use the bundled checker before constructing `CoScenarioManager`.

## Actor ownership

There are two explicit maps:

- `sumo2carla_ids`: SUMO-owned background actors mirrored into CARLA. SUMO
  advances them; CARLA receives their transforms and does not control their
  physics in the bridge spawn path.
- `carla2sumo_ids`: CARLA-owned actors, including OpenCDA CAVs. CARLA applies
  their controls; their transforms are sent back to SUMO each step.

Never manually apply a control policy to a SUMO-owned mirror or treat a mirror
as a second independent actor. Actor creation/destruction is reconciled in the
same direction as ownership. The bridge also maps vehicle types, transforms,
lights, traffic-light landmarks, and the SUMO network offset.

## One two-way tick

The repository's `CoScenarioManager.tick()` is a two-phase barrier, not two
independent application ticks:

1. **SUMO advances first.** `traci.simulationStep()` runs one SUMO step and
   updates traffic-light subscriptions and departed/arrived sets.
2. **SUMO → CARLA.** New SUMO vehicles are subscribed and spawned as CARLA
   mirrors; arrived mirrors are destroyed; every remaining SUMO actor's mapped
   transform is applied to CARLA.
3. **CARLA advances second.** `world.tick()` commits one synchronous CARLA
   frame and refreshes CARLA vehicle spawn/destruction sets.
4. **CARLA → SUMO.** New CARLA actors are added to SUMO with bridged vehicle
   types; destroyed mapped actors are removed; each CARLA-owned actor's
   transform is sent to SUMO with `moveToXY`.
5. **Signals and shared state.** CARLA traffic-light states are mapped back to
   common SUMO landmarks, and the CAV world receives the SUMO-to-CARLA map.

Typical OpenCDA scenarios call `scenario_manager.tick()` once, then update
platoon/member information, compute controls, and apply those controls. The
controls affect the next CARLA frame; do not call `world.tick()` separately in
that loop or the two simulators will drift by a frame. A useful mental model is
`SUMO(t) -> mirror CARLA(t) -> CARLA commit(t) -> CAV state/control -> SUMO
inputs for t+1`.

## Lifecycle and limits

Create CAV/platoon managers after the co-simulation manager has initialized the
world and bridge. Close in reverse order: stop/destroy scenario actors and CAV
state, then close the co-simulation manager so mapped actors and TraCI are
released. Keep one client order and one synchronous owner per simulator.

This bridge is an integration layer, not a validated synchronization proof.
Coordinate offsets, map geometry, traffic-light landmark IDs, vehicle
blueprint/type mapping, missing actors, and asynchronous external clients can
still invalidate a run. Native co-sim candidates remain external-gated because
no CARLA server, SUMO server/binary, or TraCI runtime was verified.
