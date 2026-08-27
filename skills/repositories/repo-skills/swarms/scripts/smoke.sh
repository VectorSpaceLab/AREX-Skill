#!/usr/bin/env bash
set -euo pipefail

python - <<'PY'
from importlib.metadata import version
from swarms import Agent, SequentialWorkflow, SwarmRouter

print(f"swarms version: {version('swarms')}")
print(f"Agent: {Agent.__name__}")
print(f"SequentialWorkflow: {SequentialWorkflow.__name__}")
print(f"SwarmRouter: {SwarmRouter.__name__}")
PY

swarms --help >/dev/null
printf 'swarms smoke check passed\n'
