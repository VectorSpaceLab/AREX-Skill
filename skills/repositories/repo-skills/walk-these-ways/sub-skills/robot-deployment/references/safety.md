# Physical safety and stop gates

This is the first reference to read. The repository controls a real Unitree Go1
in low-level mode; a static review or artifact check is not a safety clearance.
If the physical prerequisites are absent, mark the deployment
`BLOCKED_REQUIRED_BACKEND` and stop at preparation.

## Required physical state

Before an approved operator even considers starting the SDK or controller:

- Use a Unitree Go1 Edu and the operator's current Unitree low-level-control
  safety guidance. Suspend the robot so its feet cannot contact a person,
  obstacle, table, cable, or floor during calibration and first policy tests.
- Clear the area of people, animals, loose objects, and trip hazards. Establish a
  named operator and a second observer/emergency-stop owner where local safety
  procedure requires it. Keep the operator able to cut power immediately.
- Do not plug Ethernet, USB, or other hardware into the robot's back during
  initial calibration or a new-policy test. The README specifically calls out a
  fall/injury risk from doing so.
- Keep all software side effects out of the preparation phase: no target
  publishing, SDK launch, container launch, SSH transfer, Docker image load, or
  network mutation from this skill.

## Damping-mode gate

The README's controller sequence is `[L2+A]`, then `[L2+B]`, then
`[L1+L2+START]`. Use the physical controller and verify that the robot is on the
ground with joints moving freely before proceeding. Do not substitute an
unverified button mapping or proceed because a process appears to have started.
If damping mode does not take effect, stop and use the vendor procedure; do not
probe the motors with a new policy.

## Calibration R2 gates

`DeploymentRunner.calibrate()` uses the RC right-lower-right switch, which the
source represents as an R2 press, for **two separate approvals**:

1. With the robot suspended and the operator ready, the first R2 permits the
   slow move from the current joint offsets to the configured nominal pose. The
   normal final target is zero offset; the `low=True` emergency path uses the
   source's low pose `[hip=0, thigh=0.3, calf=-0.7]` repeated for four legs.
2. After the source reports `Starting pose calibrated`, a second R2 permits the
   controller loop. A stale press, missing edge, or unexpected pose is not an
   approval—release and re-establish the safe state.

The source moves the calibration target in small bounded increments and waits
between updates, but this is not a guarantee against hardware or configuration
faults. Keep the robot suspended and the emergency stop available through both
gates.

## PowerProtect and emergency orientation

The README says the Unitree SDK safety layer is configured with **PowerProtect
level 9**, intended to cut motor power when joint torque is too high. Treat this
as a last protective layer, not permission to run near people or to bypass the
suspension/approval gates.

During the runner loop, if `abs(roll) > 1.6` or `abs(pitch) > 1.6` radians, the
source invokes a non-waiting low-pose calibration attempt. This orientation
threshold is an emergency behavior to understand during review, not a safe
recovery guarantee. On a real event: stop the experiment, cut power according
to the approved procedure, keep clear, and inspect the robot before any reset.
Do not repeatedly restart after a tilt, torque protection event, lost state, or
unexpected joint target.

## Approval checklist

An operator must explicitly confirm each item in a deployment record:

- [ ] Go1 Edu and compatible SDK/runtime are present; otherwise
      `BLOCKED_REQUIRED_BACKEND`.
- [ ] Robot is suspended, area is clear, observer and emergency-stop plan are
      in place.
- [ ] Damping mode was verified with the physical RC sequence.
- [ ] Policy artifact and configuration were read-only validated and reviewed.
- [ ] LCM URL, interface, architecture, and message modules match the target.
- [ ] Transfer, SDK start, Docker/container start, calibration R2 #1, and R2 #2
      each have separate human approval.
- [ ] PowerProtect is available and no cable is being added at the robot rear.
- [ ] Stop criteria, log destination, and rollback artifact are recorded.

Any unchecked item is a stop. The generated skill does not provide a force,
position, or emergency-stop command.
