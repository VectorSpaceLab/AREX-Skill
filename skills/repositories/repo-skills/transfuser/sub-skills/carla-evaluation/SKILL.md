---
name: carla-evaluation
description: "Plans and diagnoses TransFuser CARLA 0.9.10.1 evaluation, Longest6
  runs, result parsing, checkpoint inspection, and guarded Docker submission
  packaging without launching external runtimes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CARLA Evaluation

Use this sub-skill for TransFuser evaluation command construction, Longest6
route selection, result interpretation, CPU-only result analysis, and Docker
submission layout checks.

## Runtime Boundary

- CARLA 0.9.10.1, a running CARLA server, the matching leaderboard and
  ScenarioRunner trees, model checkpoints, and GPU-capable inference are
  external requirements for a real driving evaluation.
- Docker builds, container execution, downloads, Alpha authentication, and
  cloud submission are external, side-effecting operations. This skill never
  performs them.
- CPU-only command construction, path preflight, JSON inspection, schema
  validation, CSV aggregation, and optional SVG map generation are available
  through the bundled helpers.
- A generated command is a plan, not proof that CARLA or the agent can run.

## Route By Task

1. For environment variables, evaluator choice, resume behavior, and a
   copyable command plan, read
   [evaluation-workflow.md](references/evaluation-workflow.md), then run
   `python scripts/build_evaluation_command.py --help`.
2. For the 36-route Longest6 benchmark, split-route selection, result
   aggregation, CSV output, map overlays, and parser abort policy, read
   [longest6-and-results.md](references/longest6-and-results.md), then run
   `python scripts/parse_results.py --help`.
3. For checkpoint structure, route/global scores, infractions, progress,
   eligibility, and status semantics, read
   [result-schema.md](references/result-schema.md), then run
   `python scripts/inspect_result_json.py --help`.
4. For image staging and submission readiness, read
   [docker-and-submission.md](references/docker-and-submission.md), then run
   `python scripts/check_submission_layout.py --help`. The helper checks only
   local files; it does not invoke Docker or Alpha.
5. For failures involving imports, server connectivity, stale checkpoints,
   parser rejection, Docker context, or credentials, read
   [troubleshooting.md](references/troubleshooting.md).

## Safe Operating Sequence

1. Decide whether the target is the TransFuser-modified local evaluator or the
   upstream evaluator. Longest6 comparisons normally require the local path.
2. Select the combined 36-route XML or one split-route XML, then choose a fresh
   checkpoint or a checkpoint that is intentionally being resumed.
3. Run the command builder with preflight enabled. Resolve every reported
   error before taking its printed command to the external CARLA runtime.
4. After the external run, inspect the result JSON before aggregating it.
5. Parse only schema-valid, route-complete result sets. Treat parser nonzero
   exit status as an abort, not as a partial success.
6. Run the Docker layout checker before any external image build. Keep
   credentials and unrelated secrets outside the build context.

## Invariants

- Do not claim a successful evaluation from a generated command or a valid
  checkpoint schema.
- Do not mix local-evaluator and upstream-evaluator scores without labeling the
  evaluator semantics.
- Do not set `--resume=False` on the legacy evaluator: its `argparse` boolean
  conversion treats any nonempty string as true. The bundled builder omits the
  flag for a fresh run.
- Do not infer benchmark success from `eligible: true`; inspect route statuses,
  progress, and `entry_status` together.
- Do not expose Alpha credentials, tokens, or private registry configuration in
  commands, reports, Dockerfiles, or staged trees.
