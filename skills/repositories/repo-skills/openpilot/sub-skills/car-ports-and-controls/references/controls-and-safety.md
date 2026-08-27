# Controls and Safety Reference

## Safety posture

openpilot implements driver-assistance features such as Adaptive Cruise Control, Automated Lane Centering, Forward Collision Warning, Lane Departure Warning, and Driver Monitoring. A driver must remain alert and ready to take control. Skill guidance must not instruct users to disable driver monitoring, bypass excessive actuation checks, or weaken panda safety requirements.

Forks that modify safety behavior need explicit safety-test evidence. If code under opendbc safety or actuator limits changes, insist on preserving and running the relevant safety suite before making claims.

## Controller and state-machine evidence

Representative CPU-safe tests:

- `openpilot/selfdrive/controls/tests/test_longcontrol.py` validates longitudinal state transitions.
- `openpilot/selfdrive/controls/tests/test_latcontrol.py` checks lateral controller saturation behavior for representative platforms/controllers.
- `openpilot/selfdrive/selfdrived/tests/test_state_machine.py` validates openpilot state transitions under enable/disable/noEntry/override events.
- `openpilot/selfdrive/monitoring/test_monitoring.py` covers driver-monitoring alert levels, lockout, recovery, and low-speed behavior.

Use these tests to validate reasoning about control-state changes before selecting route replay or live vehicle tests.

## Debugging safety with replay

The repo documents a replay-drive plus LLDB safety debugging workflow. Treat it as advanced maintainer work:

1. Use a short route.
2. Start replay in a controlled debug configuration.
3. Attach LLDB quickly before replay consumes relevant messages.
4. Set breakpoints in the relevant safety mode C files.
5. Step through Python replay and C safety code.

This workflow needs a prepared checkout, route data, compiled native code, and debugger integration. Do not run it as routine verification.

## Control tuning and reports

Lateral and longitudinal maneuver tools command real vehicle behavior in special modes. They are useful for tuning evidence, but collection is safety-critical. Report generation from an uploaded route is CPU/log analysis; data collection in a vehicle requires explicit safe area, device state, mode parameter, driver attention, and route upload confirmation.
