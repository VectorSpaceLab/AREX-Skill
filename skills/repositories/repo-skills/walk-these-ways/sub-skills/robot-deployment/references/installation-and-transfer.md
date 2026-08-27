# Installation, transfer, checkpoints, and rollback

This is a **distilled operator plan**, not an executable installation guide.
The repository's `send_to_unitree.sh`, installer, autostart scripts, and Docker
Makefile are side-effect evidence only. Do not run them from a Researcher
session or turn them into a bundled launcher.

## Prerequisites and stop conditions

Before an operator approves any transfer:

- Use a physically controlled Go1 Edu test setup and complete
  [safety.md](safety.md). Real deployment remains `BLOCKED_REQUIRED_BACKEND`
  without the robot, compatible SDK/LCM process, target host, and operator.
- Connect the development host to the robot over the approved Ethernet path and
  verify the intended `192.168.123.x` addressing and multicast interface with a
  read-only report. The README's example robot host is `192.168.123.15`; do not
  assume that address for another unit.
- Obtain credentials through the organization's approved secret mechanism. The
  source uses a `unitree` account; this skill never stores passwords, private
  keys, tokens, or private environment paths.
- Stage an already-approved deployment image and artifacts. The README notes a
  roughly 3.5 GB deployment image; do not download multi-GB data during a
  preparation task. Check free disk before transfer, image load, and extraction;
  the source reports that some Jetson disks cannot hold both the tar and expanded
  image.
- Confirm target architecture (Jetson ARM/aarch64 versus external x86), matching
  `lcm_position` build, LCM schema fingerprints, Docker/NVIDIA runtime, and
  display needs. Architecture mismatch is a stop.

## Human-run SSH → rsync → Docker/SDK sequence

When the operator has separately approved every unsafe action, the source's
intended sequence is:

1. **SSH access (UNSAFE):** authenticate to the approved robot host and verify
   hostname, account, disk, architecture, and free space. Never paste
   credentials into a command or log.
2. **Rsync transfer (UNSAFE):** transfer the selected `go1_gym_deploy` package,
   setup metadata, and the reviewed run/checkpoint subset. Exclude unrelated
   large artifacts and secrets. Record a manifest/hash before and after; do not
   overwrite the known-good release in place.
3. **Docker installation (UNSAFE):** on the robot host, an operator may load the
   pre-staged deployment image and perform the repository installer flow. The
   installer is interactive and requires privileged Docker access. Verify image
   tag/digest and available disk before extraction.
4. **SDK/controller startup (UNSAFE):** follow the order in
   [controller-workflow](controller-workflow.md): SDK-side LCM bridge first,
   then the container/controller, then the two physical R2 gates. Do not use
   `docker run`, `sudo`, SSH, rsync, or an SDK executable supplied by this
   skill.

The source transfer script downloads the image if absent and uses rsync over
SSH; both are intentionally excluded here because they mutate remote state and
can consume gigabytes. Treat any copied `deployment_image.tar` as an input with
an external provenance/checksum, not as a file this skill can obtain.

## Checkpoint and rollback protocol

Create a human-reviewed release record before changing the target:

- previous deployment image digest/tag and controller package manifest;
- previous policy label and hashes/sizes of all three required policy artifacts;
- new policy label, config provenance, architecture, LCM URL/interface, and
  expected observation/action/history shapes;
- available disk before/after each image or checkpoint operation;
- operator, approval time, stop criteria, and log location.

Transfer into a versioned staging location first. Validate the staged manifest
and policy artifacts without starting the controller. Only after approval may
the operator switch the controller's selected release. Keep the previous image,
package, and policy available until a suspended, approved test is complete.

Rollback means: stop the approved controller according to the physical
procedure, restore the prior known-good controller/image/checkpoint selection,
verify its manifest and architecture, and repeat the safety/calibration gates.
Do not delete the old release to reclaim disk during an active investigation.
If disk pressure prevents retaining a rollback, stop and ask the operator to
choose a safe storage plan; never make an unreviewed cleanup or overwrite.

## No implicit success

Successful SSH, rsync, Docker load, or process startup does not prove LCM state,
policy shape, safe calibration, or motor behavior. The handoff must retain
`BLOCKED_REQUIRED_BACKEND` until a qualified human observes the hardware gates
and accepts the physical test.
