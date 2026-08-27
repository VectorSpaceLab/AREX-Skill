# Platooning and V2X

## Data and ownership

Each CAV owns a `V2XManager`. It keeps a bounded history of ego transforms and
speeds, a nearby-CAV dictionary, and a `PlatooningPlugin`. `update_info(ego_pos,
ego_spd)` records the current state, searches the CAV world for other vehicles
within `communication_range`, and updates the plugin with the unmodified local
pose/speed. `get_ego_pos()` and `get_ego_speed()` are the peer-facing views:
configured lag selects an older sample and Gaussian location/yaw/speed noise is
then applied. Do not use those processed peer views as the local vehicle's
truth. The local plugin state is deliberately updated without communication
noise or lag.

The communication model is intentionally simple, not a wireless protocol:
`enabled` gates cooperation; `communication_range` gates discovery; `lag` is a
history offset; `loc_noise`, `yaw_noise`, and `speed_noise` are independent
noise scales. A peer can disappear or become stale when it leaves range, and
there is no verified delivery/packet-loss model beyond these concepts. Treat a
configured lag/noise value as an experiment parameter and record units (pose
coordinates, yaw, and speed in km/h as used by this package).

## Platoon roles and state

`PlatooningManager.vehicle_manager_list` is the authoritative ordered member
list. Index 0 is the leader. The manager stores capacity, destination, center
location, leader target speed, and a temporary recovery counter. After adding or
inserting a member, call `update_member_order()` so every member's front/rear
references and leader flag match the list. The manager's joining response
rejects a full platoon; when it accepts, the leader target speed is reduced by
5 (package speed units) for 200 steps and the requesting CAV is placed on the
leader's whitelist.

The FSM values are:

- `SEARCHING`: standalone CAV looks for a candidate platoon.
- `OPEN_GAP`: an existing member expands its following gap.
- `MOVE_TO_POINT` then `JOINING`: cut-in candidate approaches and changes lane.
- `BACK_JOINING`, or `FRONT_JOINING`: alternate joining maneuvers.
- `MAINTINING` (spelling is part of the API): member follows its front vehicle.
- `LEADING_MODE`: leader uses normal behavior-agent driving.
- `JOINING_FINISHED`: transition helper inserts the CAV and reorders members.
- `CUT_IN_TO_BACK`, `ABONDON`, and `DISABLE`: fallback, abandon, and CDA-off
  states; `ABONDON` is also spelled that way in the source API.

A CAV with CDA disabled is put in `DISABLE` and follows the base behavior agent
rather than joining. A searching CAV selects the nearest eligible platoon in
its discovered peer set, checks capacity and blacklist, and chooses a front,
cut-in, or back joining relation from relative distance/angle. Joining may
switch to back joining when an obstacle blocks a cut-in. A successful join
updates the manager list through `set_member()` and `update_member_order()`.

## Following, merge, and stability

`inter_gap` is a desired time-gap parameter. Maintaining members derive a target
trajectory from the front member's local-planner trajectory; the follower uses
the configured gap and adjusts prediction timing when the follower is faster.
`open_gap` is increased gradually by an `OPEN_GAP` member until the joining CAV
can enter. The merge path regenerates a route toward a point just beyond the
front vehicle and temporarily disables collision detection for the lane-change
segment; this is a live CARLA maneuver, not an offline planner guarantee.

`PlatoonDebugHelper` records speed, acceleration, TTC, time gap, and distance
gap after the initial 100 samples. The existing offline test only checks helper
containers, one update, and that `evaluate()` returns a figure and text; it
does not prove closed-loop stability. For a stability experiment, inspect
member time/distance gap traces after filtering startup samples and state the
map, target gap, speed profile, communication settings, CARLA version, and
whether positions are ground truth or peer-processed values.

## Safe use checklist

1. Enable the V2X/platooning application and provide the platoon parameters
   (`max_capacity`, `inter_gap`, `open_gap`, `warm_up_speed`) in the scenario
   configuration.
2. Create the platoon manager and set its leader before adding members.
3. Update all members before running their controls; apply controls only after
   the step's information has been refreshed.
4. Do not infer a successful merge merely from an FSM value: verify lane,
   ordering, front/rear references, gap traces, and collision outcome.
5. If communication is disabled or unavailable, expect normal single-vehicle
   behavior rather than a partial platoon.
