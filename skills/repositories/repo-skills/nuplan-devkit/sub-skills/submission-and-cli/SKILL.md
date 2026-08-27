---
name: submission-and-cli
description: "Operate the nuPlan database CLI and the v1.2.2 planner submission
  boundary: inspect databases, configure a Hydra submission planner, preserve
  the gRPC contract, package a container, and diagnose safe submission
  failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Submission and CLI

Use this route when the task concerns `nuplan_cli`, database inspection,
submission packaging, planner serving, gRPC/EvalAI protocol behavior, Docker
Compose integration, or a submission error. This is an operating guide for
nuPlan-devkit 1.2.2 (Python 3.9+); it is not a replacement for the planner,
simulation, map, or scenario APIs.

## Route the request

- **CLI or DB inspection:** read [CLI reference](references/cli-reference.md).
  Help and command parsing do not require a dataset; do not let a missing
  default DB cause an automatic download merely to show help.
- **Planner implementation or trajectory semantics:** read
  [submission contract](references/submission-contract.md), then hand detailed
  `AbstractPlanner`, simulation, controller, and metric questions to the
  `simulation-and-evaluation` route.
- **Container, gRPC, protocol, or EvalAI failure:** read the contract and
  [troubleshooting](references/troubleshooting.md). Do not repair a protocol
  failure by editing generated challenge files.
- **Static preflight:** run the bundled checker described below. It is local,
  read-only, dependency-free, and never builds Docker, contacts EvalAI, uses
  credentials, downloads data, or modifies files.

## CLI entry point

The package installs the console script `nuplan_cli`, backed by
`nuplan.cli.nuplan_cli:main`. The top-level command currently exposes the
`db` group only:

```bash
nuplan_cli --help
nuplan_cli db --help
nuplan_cli db info --help
nuplan_cli db duration --help
nuplan_cli db log-duration --help
nuplan_cli db log-vehicle --help
nuplan_cli db scenarios --help
```

Each DB command takes an optional positional `DB_VERSION` (a local database
path or a path accepted by the package's data helper) and the `--data-root`
option. The five commands are `info`, `duration`, `log-duration`,
`log-vehicle`, and `scenarios`; exact output and defaults are in the CLI
reference. A real query calls the package's download helper when the selected
path is absent, so pass an existing local file or stop at `--help` when the
user asked only for syntax.

## Submission workflow

1. Make the custom planner work through the normal simulation route first.
   It must implement the `AbstractPlanner` contract and should not require a
   scenario object for a competition submission.
2. Add or select a Hydra planner config. The submission launcher uses
   `default_submission_planner`, requires `planner=...`, seeds through
   `cfg.seed`, constructs `SubmissionPlanner(cfg.planner)`, and serves gRPC.
3. Edit only the intended planner/config and the marked planner selection in
   `entrypoint_submission.sh`. Add dependencies to `requirements_submission.txt`
   and copy model assets from the Docker build context when necessary.
4. Preflight the manifest with the safe checker. Confirm trajectory signals,
   monotonic timestamps, at least two points, and at least an 8-second horizon.
5. If Docker is available, build and run the local submission/simulation
   composition as an optional integration check. Set the three host roots
   expected by Compose and verify that maps are available; this route does not
   claim a Docker or full-dataset verification.
6. Treat EvalAI upload and remote execution as external, credentialed,
   side-effecting actions. Verify the exact phase and image tag in the user's
   competition UI before using the documented `evalai push` command.

## Hard protocol boundaries

The following are organizer-owned or generated and must remain unchanged:

- `nuplan/submission/protos/challenge.proto`
- `nuplan/submission/challenge_pb2.py`
- `nuplan/submission/challenge_pb2_grpc.py`
- `nuplan/submission/submission_container.py`
- `nuplan/submission/submission_planner.py`

Do not patch these files to solve version, port, serialization, or timeout
errors. The allowed customization is the planner implementation/configuration,
its declared dependencies/assets, and the intended planner-selection portion
of `entrypoint_submission.sh`. The checker rejects protected paths declared as
changed.

## Safe static checker

Use the bundled [static checker](scripts/check_submission_manifest.py). From the
repository root, create a JSON manifest and run:

```bash
python skills/disco/nuplan-devkit/sub-skills/submission-and-cli/scripts/check_submission_manifest.py \
  --root . --manifest submission-manifest.json
python skills/disco/nuplan-devkit/sub-skills/submission-and-cli/scripts/check_submission_manifest.py \
  --root . --manifest submission-manifest.json --quiet
```

The manifest format and all checks are documented in the contract. A zero exit
status means only that the declared static facts pass; it does not prove a
planner can initialize, compute within the one-second iteration budget, access
maps, or run in Docker. A nonzero result is actionable and should be fixed
before any build or upload.

## Stop conditions and handoff

Stop and ask for clarification when the requested phase, image tag, dataset
root, map availability, or intended planner config is unknown and affects a
side-effecting action. Report missing data separately from protocol defects.
Never download a dataset in a help-only path. Never put tokens, private paths,
inspection environment names, generated reports, or checkout links into a
runtime instruction or manifest example.

For every handoff, state: command attempted, selected DB/config/image, whether
this was help-only, local, or remote, exact failure surface, and which checks
remain unverified. Keep detailed symptoms and recovery recipes in
[troubleshooting](references/troubleshooting.md).
