# Tracing, Telemetry, Logs, Outputs, and Fingerprints

This reference covers CrewAI's built-in tracing switch, anonymous package telemetry, local output logs, latest kickoff task-output storage, and fingerprint fields that are useful for observability and audit workflows.

## Built-In CrewAI Tracing

CrewAI has a built-in trace collection listener for Crews and Flows. It records execution lifecycle events such as crew kickoff start/completion/failure, flow start/finish, method execution, agent/task lifecycle, tool usage, LLM calls, memory/knowledge events, reasoning events, and selected system events.

Enablement priority is:

1. Explicit runtime override: `Crew(..., tracing=True|False)` or `Flow(..., tracing=True|False)`.
2. Environment variable: `CREWAI_TRACING_ENABLED=true` or `CREWAI_TRACING_ENABLED=1` enables tracing when no explicit override is set.
3. Stored user tracing consent from CrewAI user data, used only when no explicit override or env enablement applies.

Important consequences:

- `tracing=True` on a Crew/Flow enables tracing even if `CREWAI_TRACING_ENABLED` is unset.
- `tracing=False` on a Crew/Flow disables tracing for that execution even if the env var says to enable it.
- `CREWAI_TRACING_ENABLED=false` does not override `Crew(tracing=True)` or `Flow(tracing=True)`.
- The trace listener is event-bus based; repeated process imports, notebooks, or tests can look like duplicate traces if they run multiple traced executions or retain previously registered listeners.

### Minimal Crew Example

```python
from crewai import Agent, Crew, Process, Task

agent = Agent(role="Observer", goal="Summarize status", backstory="Tracks project state")
task = Task(description="Summarize the current status", expected_output="Short summary", agent=agent)

crew = Crew(
    agents=[agent],
    tasks=[task],
    process=Process.sequential,
    tracing=True,
    verbose=True,
)

result = crew.kickoff(inputs={"topic": "release readiness"})
```

### Minimal Flow Example

```python
from crewai.flow.flow import Flow, listen, start

class StatusFlow(Flow):
    def __init__(self):
        super().__init__(tracing=True)

    @start()
    def collect(self):
        return "collected"

    @listen(collect)
    def report(self, value):
        return f"status: {value}"
```

Use [flows-and-events](../../flows-and-events/SKILL.md) for flow graph mechanics; use this reference only for trace enablement and observability behavior.

## Anonymous Telemetry

CrewAI also initializes OpenTelemetry-based anonymous package telemetry unless disabled. The default telemetry exporter is an OTLP HTTP exporter with CrewAI's service name. The telemetry module is defensive: exporter failures are caught so telemetry failures should not break user code.

Disable anonymous telemetry with any of:

```bash
export OTEL_SDK_DISABLED=true
export CREWAI_DISABLE_TELEMETRY=true
export CREWAI_DISABLE_TRACKING=true
```

Telemetry privacy behavior:

- Default package telemetry is documented as not collecting prompts, task descriptions, agent backstories/goals, responses, or sensitive data.
- `share_crew=True` expands data captured in telemetry spans, including agent roles/goals/backstories, task descriptions/expected outputs, task outputs, and final crew output. Use it only when the user intends to share fuller execution details.
- Fingerprint UUIDs and fingerprint metadata can be attached to telemetry spans; avoid putting secrets or high-cardinality private data in fingerprint metadata.

## Trace Batch Behavior

CrewAI trace batches are initialized and finalized around top-level Crew or Flow execution. The trace system has safeguards for nesting:

- A Flow that owns a batch should not let a nested Crew reclaim or finalize that Flow's batch.
- A nested Flow or Crew can produce events inside the parent trace context without taking over batch ownership.
- Event handlers are waited on briefly during finalization; if pending handlers time out, events may be incomplete and the batch can be marked failed.
- Backend authentication failures can fall back to ephemeral tracing in supported paths; hosted dashboards still require the user to be authenticated or configured.

## Output Logs

`Crew(output_log_file=...)` writes local task start/completion logs without needing hosted tracing.

Supported values:

- `True`: write `logs.txt` in the current working directory.
- A string ending in `.json`: append structured JSON log entries to that JSON file.
- A string ending in `.txt`: append text log lines to that text file.
- A string with no `.json`/`.txt` suffix: CrewAI appends `.txt`.
- `False` or `None`: no output log file is written.

Log entries include timestamps and task fields such as task name, task description, agent role, status, and completed output. Treat log files as potentially sensitive because task descriptions and outputs can contain user data.

```python
crew = Crew(
    agents=[agent],
    tasks=[task],
    output_log_file="run-observability.json",
)
```

## Latest Kickoff Task Outputs

CrewAI stores latest kickoff task outputs in a local SQLite-backed storage handler to support replay and audit workflows. Each task record contains the task id, expected output, serialized output fields, task index, kickoff inputs, replay flag, and timestamp.

Use cases:

- Inspect the most recent task ids before replaying a run.
- Reconstruct task output order after a kickoff.
- Debug why replay starts from a particular task.

Boundaries:

- Use [cli-and-projects](../../cli-and-projects/SKILL.md) for exact `crewai log-tasks-outputs` and `crewai replay` command syntax.
- Use [core-runtime](../../core-runtime/SKILL.md) for `CrewOutput.tasks_output`, `Task.output`, and output model semantics.
- The latest kickoff store is local mutable state; do not treat it as a durable audit database for multiple historical runs.

## Fingerprints

`Agent`, `Task`, and `Crew` each expose a `fingerprint` from `crewai.security`. Fingerprints support identity/audit workflows and can be emitted in telemetry metadata.

Key facts:

- A default `Fingerprint()` generates a UUID and creation timestamp automatically.
- Direct constructor attempts to set `uuid_str` or `created_at` are ignored because those are private generated fields.
- `Fingerprint.generate(seed="stable-id")` creates a deterministic UUID for the same non-empty seed.
- Deterministic fingerprints with the same seed have the same UUID but different creation timestamps.
- `metadata` is mutable, JSON-serializable through `to_dict()`, and limited in size; nested metadata may only be one level deep.
- `SecurityConfig(fingerprint="seed")` uses the string as a deterministic fingerprint seed.
- Passing the same `SecurityConfig` instance to multiple components makes them share the same fingerprint object; this is useful only when intentionally modeling shared identity.

Example:

```python
from crewai.security import Fingerprint, SecurityConfig

fingerprint = Fingerprint.generate(
    seed="billing-agent-v1",
    metadata={"component": "billing-agent", "version": "1"},
)
security_config = SecurityConfig(fingerprint=fingerprint)

agent = Agent(
    role="Billing Observer",
    goal="Track billing workflow status",
    backstory="Audits billing workflow events",
    security_config=security_config,
)
```

## Safe Observability Checklist

- Decide whether the run should use hosted built-in tracing, local logs, latest task-output storage, third-party OpenTelemetry, or only static diagnostics.
- If a specific run must stay local, set `tracing=False` and set telemetry disable env vars before constructing Crew/Flow objects.
- Do not set `share_crew=True` unless the user accepts fuller prompt/task/output telemetry.
- Use output log files for local debugging, but redact or secure them when task inputs/outputs may be sensitive.
- Use deterministic fingerprints for stable component identity, not for secret material or user identifiers.
