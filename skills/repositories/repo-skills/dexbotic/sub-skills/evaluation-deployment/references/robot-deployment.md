# Robot deployment boundaries

## What is safe to prepare

- a deployment manifest containing server URL, checkpoint identity, camera slot map, action semantics, state dimensions, FPS, and chunk aggregation;
- a synthetic/captured-observation HTTP request to a non-actuating local server;
- conversion and schema validation of recorded data;
- topology diagrams and dependency checks.

## What requires explicit hardware approval

- serial device access, camera capture, `/dev/video*`, robot SDKs, bridge servers, gRPC clients, network control, actuator commands, and any vendor runtime;
- changing robot calibration, action limits, or control frequency;
- connecting a policy output to a real robot.

The repository's SO-101/XLeRobot/DOS-W1 bridge scripts are reference-only for this generated skill because they may access hardware or network services. Use the data-only converters only after checking their external package requirements. A bridge command copied into a new environment is not a safe substitute for a deployment plan.

## Bring-up gates

1. **Static:** validate config, checkpoint metadata, action dimensions, masks, and camera slot mapping.
2. **Server:** `/health` and `/v1/capabilities` pass with no robot attached.
3. **Captured input:** one recorded image/state request returns finite actions of the declared dimension.
4. **Bridge dry run:** vendor bridge receives and logs data without forwarding actuator commands.
5. **Low-risk motion:** only an authorized operator enables a constrained motion test with hard limits and emergency stop.

If any gate fails, stop at that gate. Do not diagnose hardware failure by changing model action semantics.
