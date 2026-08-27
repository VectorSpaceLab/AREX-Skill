---
name: xparl-distributed
description: "Guide safe PARL xparl cluster lifecycle, remote_class actors,
  parl.connect file distribution, CPU/GPU workers, monitoring, logs, and
  distributed troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# xparl Distributed

Use this sub-skill when a task involves PARL distributed execution, `xparl`,
`@parl.remote_class`, `parl.connect`, worker resources, distributed files,
cluster monitors, remote logs, or CPU/GPU actor placement.

## Safety gate

Before starting or connecting any cluster, read
[`references/security-and-operations.md`](references/security-and-operations.md).
`xparl` intentionally ships executable Python objects and file payloads to
workers; treat every worker and every submitted script as trusted-code execution.
Do not expose xparl master, monitor, or log-server ports to untrusted networks,
and do not accept untrusted workers or code.

## Route map

- For CLI lifecycle commands, port planning, local CPU/GPU worker commands, and
  help-only diagnostics, read
  [`references/cli-reference.md`](references/cli-reference.md) and use
  [`scripts/check_xparl_cli.py`](scripts/check_xparl_cli.py).
- For Python APIs, `@parl.remote_class` arguments, `wait=False` futures,
  `n_gpu`, `parl.connect(master_address, distributed_files=[])`, serialization,
  and file-distribution behavior, read
  [`references/remote-api.md`](references/remote-api.md).
- For monitor/log-server operations, shutdown boundaries, version consistency,
  and stale-process handling, read
  [`references/security-and-operations.md`](references/security-and-operations.md).
- For symptoms, likely causes, and recovery steps, read
  [`references/troubleshooting.md`](references/troubleshooting.md).
- For PARL imports, backend selection, and core `Model` / `Algorithm` / `Agent`
  usage around distributed actors, load the sibling
  [`core-framework`](../core-framework/SKILL.md) sub-skill.
- For complete distributed RL training examples and algorithm-specific actor /
  learner recipes, load the sibling
  [`algorithm-recipes`](../algorithm-recipes/SKILL.md) sub-skill after this one.

## Non-goals

This sub-skill covers xparl mechanics and operational safety. It does not choose
RL algorithms, tune training loops, or claim that an optional backend or GPU is
available. Route those decisions to the relevant sibling sub-skill and verify the
actual runtime before launching long jobs.
