# Verifiers, RewardKit, and metrics

## Harbor verifier contract

Harbor runs the task's OS-appropriate test entrypoint from `/tests` and reads
reward output from `/logs/verifier/`. The verifier checks `reward.json` first
and falls back to `reward.txt`:

```bash
#!/usr/bin/env bash
set -u
pytest /tests/test_outputs.py
status=$?
mkdir -p /logs/verifier
if [ "$status" -eq 0 ]; then
  printf '1\n' > /logs/verifier/reward.txt
else
  printf '0\n' > /logs/verifier/reward.txt
fi
exit "$status"
```

A JSON reward supports multiple numeric dimensions:

```json
{"correctness": 1.0, "style": 0.75}
```

A text reward is interpreted as the single key `reward`:

```text
0.0
```

Use absolute paths because the verifier may run from a different working
folder. Always create the reward directory if the test environment does not
provide it. Missing, empty, malformed, or non-numeric reward files are verifier
failures; an exit code alone is not a reward. Keep test scripts deterministic,
bounded, and independent of the host checkout. Do not put answer-bearing
fixtures or the reference solution where the agent can read them.

The standard verifier uploads task `tests/` into the agent environment, runs the
script, downloads verifier logs, and parses the result. A separate verifier
image owns its own test script and instead receives `/logs/artifacts/` plus the
configured artifact paths. Use a separate verifier when grader code, judge
prompts, dependencies, API keys, or clean-room state must not be exposed to the
agent.

## RewardKit setup

RewardKit is an optional independent package. A task can use it from
`tests/test.sh`:

```bash
#!/usr/bin/env bash
set -e
uvx --from 'harbor-rewardkit==0.1.*' rewardkit /tests
```

The package name and executable differ: `harbor-rewardkit` is the package;
`rewardkit` is the command. In an offline task, install or vendor the package
in the verifier image instead of relying on a network call. If a judge needs a
credential, pass it through a narrowly scoped `[verifier.env]` reference and
obtain explicit approval for any API use:

```toml
[verifier]
timeout_sec = 300.0

[verifier.env]
JUDGE_API_KEY = "${JUDGE_API_KEY}"
```

Prefer a separate verifier for judge prompts and keys. Programmatic checks that
only inspect local files can remain offline.

## Programmatic criteria

A criteria Python file imports RewardKit and registers checks:

```python
from pathlib import Path
import rewardkit as rk
from rewardkit import criterion

rk.file_exists("output.json", weight=2.0)
rk.json_key_equals("output.json", "status", "ok")
rk.command_succeeds("python -m app --check", isolated=True)

@criterion
def has_nonempty_report(workspace: Path) -> bool:
    report = workspace / "report.md"
    return report.is_file() and bool(report.read_text().strip())
```

Use built-ins for files, text/regex, commands, JSON/CSV, HTTP, images, and
trajectory checks when they express the rubric. Use `@criterion` for task-
specific boolean or float functions whose first parameter is `workspace: Path`.
Pass `weight` for intended importance. Use `isolated=True` for commands that
mutate the workspace so criteria do not affect one another.

A directory of `.py` criteria is one reward dimension by default. Subdirectories
become separate dimensions, for example:

```text
tests/
├── test.sh
├── correctness/check.py
├── structure/files_exist.py
└── quality/judge.toml
```

RewardKit writes `reward.json` and `reward-details.json`. A root `reward.toml`
can add aggregate keys such as `reward` using `weighted_mean`, `all_pass`,
`any_pass`, or `threshold`. A local `reward.toml` can weight a criteria group
or change its aggregation. Keep the aggregate name aligned with any Harbor
`min_reward` gate.

## Judge criteria

Use a TOML judge only for subjective signals that cannot be expressed
reliably as deterministic checks:

```toml
[judge]
judge = "provider/model-id"
files = ["/app/main.py"]
timeout = 300

[[criterion]]
description = "The program produces the requested result."
type = "binary"
weight = 2.0

[[criterion]]
description = "The implementation is readable."
type = "likert"
points = 5

[scoring]
aggregation = "weighted_mean"
```

Judge types include binary, likert, and numeric. Agent judges are slower and
more expensive than LLM judges. Judge/network credentials, provider routing,
trajectory evaluation, and external service calls are explicit gates; never
claim a judge was verified with only a TOML parse.

## RewardKit and multi-step tasks

Each multi-step verifier runs independently against `/tests` for its step.
RewardKit's internal dimension aggregation is separate from Harbor's
trial-level `multi_step_reward_strategy`:

- `mean` averages each reward key across steps that produced results; missing
  keys contribute zero.
- `final` uses the final step result verbatim, including its full reward dict.
- `min_reward = 1.0` gates the conventional `reward` key.
- `min_reward = { correctness = 0.8, style = 0.5 }` gates named keys; missing
  results or keys fail the gate.

Design the final reward shape before choosing the strategy. With `final`, an
abort means the aborted step's result becomes the final result, not a later
step that never ran.

## Dataset metrics

A dataset-level metric is a standalone executable script. It receives a JSONL
file through `-i/--input-path` and writes one JSON object through
`-o/--output-path`:

```bash
python metric.py -i rewards.jsonl -o metrics.json
```

The bundled mean recipe below is distilled from the Harbor metric example and
has no repository dependency:

```python
# /// script
# dependencies = []
# ///
import argparse
import json
from pathlib import Path


def main(input_path: Path, output_path: Path) -> None:
    rewards: list[float] = []
    for line in input_path.read_text().splitlines():
        value = json.loads(line)
        if value is None:
            rewards.append(0.0)
        elif len(value) != 1:
            raise ValueError(
                f"Expected exactly one key in reward dictionary, got {len(value)}"
            )
        else:
            rewards.extend(float(item) for item in value.values())
    mean = sum(rewards) / len(rewards) if rewards else 0.0
    output_path.write_text(json.dumps({"mean": mean}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-path", type=Path, required=True)
    parser.add_argument("-o", "--output-path", type=Path, required=True)
    args = parser.parse_args()
    main(args.input_path, args.output_path)
```

The input may contain `null`, which this recipe treats as zero. It rejects
multi-key reward objects so the aggregation policy is explicit. A metric may
write several numeric outputs, but keep names and missing-reward behavior
stable. Add the file to the dataset manifest as a simple `[[files]]` entry;
its digest contributes to the dataset content hash.

## Verifier selection and failure signals

- **Shell**: one or a few deterministic commands; manually write the reward.
- **Pytest**: assertion-oriented checks; translate exit status to reward.
- **RewardKit programmatic**: weighted/reusable criteria and multi-dimensional
  scores; write `reward.json` through the CLI.
- **RewardKit judge**: subjective quality or agent/trajectory grading; isolate
  grader inputs and gate credentials/network.
- **Custom Harbor verifier**: only when task-side `test.sh` is insufficient;
  subclass the verified verifier contract and route framework extension work to
  `integrations`.

Before blaming the agent, inspect: test script exit status, reward file path,
JSON shape, absolute paths, test dependencies, environment network state, and
whether a separate verifier received the declared artifacts. Result or
trajectory interpretation after a run belongs to `analyze-publish`.
