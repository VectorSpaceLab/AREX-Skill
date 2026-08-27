# Pipeline Authoring Workflow Recipes

Use these recipes to build or revise ZenML pipeline code without reopening external docs or source files. Keep examples small, typed, and importable; scale them only after the local smoke pattern works.

## Recipe: Minimal Static Pipeline

Use when the user has ordinary Python logic and wants a tracked ZenML workflow.

```python
from typing import Annotated

from zenml import pipeline, step

@step
def load_name(default: str = "ZenML") -> str:
    return default

@step
def greet(name: str) -> Annotated[str, "greeting"]:
    return f"Hello {name}!"

@pipeline(enable_cache=False)
def greeting_pipeline(name: str = "ZenML") -> Annotated[str, "greeting"]:
    selected = load_name(default=name)
    return greet(selected)

if __name__ == "__main__":
    greeting_pipeline(name="agent")
```

Checklist:

- Keep `@step` and `@pipeline` functions at module level.
- Add return annotations before debugging materializer behavior.
- Use `Annotated[..., "artifact_name"]` when the downstream code or UI needs stable output names.
- Disable cache only when the step has side effects, randomness, or a task explicitly asks for fresh execution.

## Recipe: Multi-Output Step with Per-Output Materializers

Use when a step returns multiple artifacts and each output needs distinct storage.

```python
from typing import Annotated

from zenml import pipeline, step
from zenml.materializers.base_materializer import BaseMaterializer

class ReportMaterializer(BaseMaterializer):
    ASSOCIATED_TYPES = (str,)

    def save(self, data: str) -> None:
        with self.artifact_store.open(f"{self.uri}/report.txt", "w") as handle:
            handle.write(data)

    def load(self, data_type: type[str]) -> str:
        with self.artifact_store.open(f"{self.uri}/report.txt", "r") as handle:
            return handle.read()

@step(output_materializers={"report": ReportMaterializer})
def evaluate() -> tuple[Annotated[float, "score"], Annotated[str, "report"]]:
    return 0.91, "validation passed"

@step
def publish(score: float, report: str) -> None:
    print(score, report)

@pipeline
def evaluation_pipeline() -> None:
    score, report = evaluate()
    publish(score=score, report=report)
```

Checklist:

- Match `output_materializers` keys to named outputs exactly.
- Define custom materializer classes at module scope so remote runs can import them.
- Use `self.artifact_store.open(...)` for all artifact files.
- Add dependency packages to `DockerSettings.required_integrations` or `DockerSettings.requirements` for remote containers.

## Recipe: Runtime Configuration with `with_options(...)`

Use when a task needs per-run or per-step changes without globally mutating reusable steps.

```python
from zenml import pipeline, step
from zenml.config import DockerSettings, ResourceSettings, StepRetryConfig

@step
def train(epochs: int = 3) -> str:
    return f"trained for {epochs} epochs"

@pipeline(settings={"resources": ResourceSettings(cpu_count=2, memory="2GB")})
def training_pipeline(epochs: int = 3) -> None:
    train.with_options(
        parameters={"epochs": epochs},
        retry=StepRetryConfig(max_retries=2, delay=5, backoff=2),
        settings={
            "docker": DockerSettings(
                required_integrations=[],
                requirements=["scikit-learn>=1.3"],
            ),
            "resources": ResourceSettings(gpu_count=0, memory="4GB"),
        },
    )()

training_pipeline.with_options(enable_cache=False, run_name="fresh-training")()
```

Checklist:

- Prefer `with_options(...)` inside pipeline bodies.
- Use `configure(...)` only when the same object should remain changed for all future invocations.
- Resource settings merge from pipeline to step; step values override pipeline values.
- Some orchestrators ignore resource fields; do not promise enforcement without checking the stack component.

## Recipe: YAML or External Config Feeding Pipeline Parameters

Use when a user wants Hydra, YAML, or another config manager to decide values while ZenML handles orchestration.

```python
from zenml import pipeline, step

@step
def train_model(learning_rate: float, batch_size: int) -> None:
    print(f"lr={learning_rate}, batch={batch_size}")

@pipeline
def training_pipeline(learning_rate: float = 0.01, batch_size: int = 32) -> None:
    train_model(learning_rate=learning_rate, batch_size=batch_size)

def run_from_dict(config: dict) -> None:
    zenml_config = config.get("zenml", {})
    training_pipeline.with_options(
        enable_cache=zenml_config.get("enable_cache", True),
        settings=zenml_config.get("settings", {}),
    )(
        learning_rate=config["training"]["learning_rate"],
        batch_size=config["training"]["batch_size"],
    )
```

Checklist:

- Convert third-party config objects to plain Python dictionaries before passing them to ZenML.
- Keep step parameters JSON-serializable.
- Pass complex config files or model objects as artifacts if they are not JSON-serializable.
- Do not mix mutable global config with `configure(...)` unless the task explicitly wants process-wide mutation.

## Recipe: Dynamic Map/Reduce

Use for runtime-dependent fan-out over a list artifact.

```python
from zenml import pipeline, step, unmapped

@step
def produce_items() -> list[int]:
    return [1, 2, 3]

@step
def multiply(value: int, factor: int) -> int:
    return value * factor

@step
def reduce_values(values: list[int]) -> int:
    return sum(values)

@pipeline(dynamic=True, enable_cache=False)
def map_reduce_pipeline(factor: int = 2) -> None:
    items = produce_items()
    doubled = multiply.map(value=items, factor=unmapped(factor))
    reduce_values(doubled)
```

Checklist:

- Use `map(...)` when all mapped inputs have the same length.
- Use `product(...)` for Cartesian product fan-out.
- Wrap sequence-like values in `unmapped(...)` when each mapped invocation should receive the whole object.
- Add `get_item_count(...)` and `load_item(...)` to custom materializers before mapping over custom sequence artifacts.

## Recipe: Manual Dynamic Loop with `.load()` and `.chunk()`

Use when Python control flow must inspect an upstream artifact before deciding downstream work.

```python
from zenml import pipeline, step

@step
def produce_numbers() -> list[int]:
    return [1, 2, 3, 4]

@step
def process_even(value: int) -> int:
    return value * 10

@pipeline(dynamic=True)
def selective_pipeline() -> None:
    numbers = produce_numbers()
    for index, value in enumerate(numbers.load()):
        if value % 2 == 0:
            process_even(numbers.chunk(index=index))
```

Checklist:

- `.load()` reads concrete data into the orchestration environment and should be used only for decisions.
- `.chunk(index=...)` creates the DAG edge to a downstream step; do not pass loaded values when lineage matters.
- Avoid loading very large artifacts in the orchestration process. Use `map(...)` or a filtering step when possible.

## Recipe: Concurrent Dynamic Steps

Use when a dynamic pipeline should launch independent work in parallel.

```python
from zenml import pipeline, step

@step(runtime="isolated")
def score_item(item: int) -> int:
    return item * item

@step
def summarize(values: list[int]) -> None:
    print(sum(values))

@pipeline(dynamic=True)
def concurrent_pipeline() -> None:
    futures = [score_item.submit(item=item) for item in [1, 2, 3]]
    results = [future.result() for future in futures]
    summarize(results)
```

Checklist:

- `runtime="isolated"` asks the orchestrator for separate execution environments where supported.
- `runtime="inline"` runs in the orchestration environment, often as threads for submitted steps.
- Call `future.wait()` when no output is needed; call `future.result()` when passing outputs downstream.
- Use explicit `after=` dependencies for side-effect-only ordering.

## Recipe: Dynamic Child Pipelines

Use when a parent dynamic pipeline should reuse a child workflow.

```python
from zenml import pipeline, step

@step
def produce_number() -> int:
    return 7

@pipeline(dynamic=True)
def child_pipeline() -> int:
    return produce_number()

@step
def consume_number(value: int) -> None:
    print(value)

@pipeline(dynamic=True)
def parent_pipeline() -> None:
    child_output = child_pipeline()
    consume_number(child_output)

@pipeline(dynamic=True)
def concurrent_parent_pipeline() -> None:
    future = child_pipeline.submit()
    consume_number(future.result())

@pipeline(dynamic=True)
def inline_parent_pipeline() -> None:
    child_output = child_pipeline.embed()
    consume_number(child_output)
```

Choose the call mode deliberately:

- `child_pipeline(...)`: synchronous child run with child pipeline configuration applied.
- `child_pipeline.submit(...)`: concurrent child run with child pipeline configuration applied.
- `child_pipeline.embed(...)`: inline reuse without a child run; parent configuration governs inline steps.

Checklist:

- Keep child pipeline calls in a stable order across retries and resumes.
- Do not insert a new child call before existing child calls in a deployed or resumable pipeline unless reruns are acceptable.
- Put shared dependencies in the parent image/source bundle; children do not trigger separate Docker builds.
- If child-specific Docker settings, retry settings, tags, or hooks matter, do not use `embed(...)`.

## Recipe: Wait/Resume Human Approval

Use when a dynamic pipeline must pause for human or external input.

```python
from pydantic import BaseModel
from zenml import pipeline, step, wait

class Approval(BaseModel):
    approved: bool
    release_tag: str

@step
def prepare_candidate() -> str:
    return "model:v17"

@step
def register_release(candidate: str, release_tag: str) -> None:
    print(f"Registering {candidate} as {release_tag}")

@pipeline(dynamic=True)
def approval_pipeline() -> None:
    candidate = prepare_candidate()
    approval = wait(
        schema=Approval,
        question="Approve this candidate?",
        timeout=600,
        name="release_approval",
        metadata={"candidate": "model:v17"},
    )
    if approval.approved:
        register_release(candidate=candidate, release_tag=approval.release_tag)
```

Checklist:

- `wait(...)` belongs in the dynamic pipeline body, not inside a step.
- Resolve the wait condition before trying to resume the run.
- In nested workflows, resume the parent run when the CLI or UI says the paused run is a child.
- If the run should pause quickly, make sure concurrent futures and child runs have settled before calling `wait(...)`.

## Recipe: Lifecycle Hooks and Custom Hook Invocations

Use when a user wants notifications, custom observability records, or lifecycle side effects.

```python
from typing import Optional

from zenml import get_step_context, pipeline, run_hook, step


def notify_failure(exception: Optional[BaseException] = None) -> None:
    context = get_step_context()
    print(f"{context.step_run.name} failed: {exception}")


def record_tool_call(tool_name: str) -> str:
    return f"called {tool_name}"

@step(on_failure=notify_failure)
def agent_step() -> str:
    return run_hook(record_tool_call, "search", store_return=True)

@pipeline
def hooked_pipeline() -> None:
    agent_step()
```

Checklist:

- `on_start` and `on_success` hooks take no arguments.
- `on_failure` and `on_end` hooks may accept an optional exception argument.
- Cache hits skip step-level hooks; disable cache when validating hook behavior.
- Hook failures are recorded and swallowed, so test alert code directly if the run must fail on alert failure.
- Static pipeline-level hooks are defaults for steps; dynamic pipeline-level hooks run once at run scope.

## Recipe: Scheduled Pipeline

Use when a supported orchestrator should trigger future runs.

```python
from datetime import datetime, timedelta

from zenml import pipeline, step
from zenml.config import Schedule

@step
def refresh_features() -> None:
    print("refreshing")

@pipeline
def feature_pipeline() -> None:
    refresh_features()

schedule = Schedule(
    name="feature-refresh-hourly",
    start_time=datetime.now().astimezone(),
    interval_second=timedelta(hours=1),
    catchup=False,
)
feature_pipeline.with_options(schedule=schedule)()
```

Checklist:

- Confirm the active orchestrator supports schedules before promising execution.
- Prefer timezone-aware datetimes.
- Use `catchup=False` unless the pipeline is explicitly designed for backfills.
- Local and local Docker orchestrators do not support scheduled runs.
- Schedule update/delete/activate/deactivate commands are CLI/client work; route to `../cli-and-client/SKILL.md`.

## Recipe: Local Smoke Without Polluting User Configuration

Use before handing code back when the task asks for a runnable local pipeline and a ZenML package is installed.

```bash
python scripts/pipeline_smoke.py --check-imports
python scripts/pipeline_smoke.py --run
```

What the bundled smoke does:

- Sets temporary `ZENML_CONFIG_PATH`, `ZENML_LOCAL_STORES_PATH`, and `ZENML_REPOSITORY_PATH` values.
- Initializes a temporary ZenML repository.
- Runs one tiny local pipeline with two typed steps.
- Cleans up the temporary directory unless `--keep-temp` is passed.

Use `--check-imports` first when optional extras may be missing or when a remote server login is active.

## Recipe: Convert Static Pipeline to Dynamic Safely

Use when a static DAG needs runtime loops, mapping, waits, or child pipelines.

1. Move every step and pipeline function to module scope.
2. Decide whether runtime branching needs concrete values (`.load()`) or only fan-out wiring (`.map(...)`, `.product(...)`, `.chunk(...)`).
3. Add `@pipeline(dynamic=True)` and keep default execution mode unless the task needs a different failure policy.
4. Replace Python loops over ordinary step outputs with one of:
   - `step.map(...)` for full collection fan-out.
   - `for index, value in enumerate(output.load()): ... output.chunk(index=index)` for decision-based loops.
   - `step.submit(...)` plus futures for concurrency.
5. If extracting child workflows, choose `child(...)`, `child.submit(...)`, or `child.embed(...)` based on configuration isolation needs.
6. Freeze the relative order of child pipeline calls and submitted step calls before enabling wait/resume or retry-heavy usage.
7. Disable cache temporarily while validating the conversion, then re-enable it step by step.

Validation ideas:

- Run `inspect_pipeline_api.py --json` and confirm `pipeline` has `dynamic`, hooks, `execution_mode`, and `cache_policy` parameters.
- Run a tiny local version with `pipeline_smoke.py --run` if local ZenML execution is available.
- For real user code, inspect generated run/step names and child run keys after the first run; record them before changing call order.

## Recipe: Debug a Pipeline Run

Use this triage order:

1. Verify imports and installed ZenML surface with `inspect_pipeline_api.py --check-imports`.
2. Check whether the failing value is a parameter or artifact. Non-JSON parameters should become artifacts.
3. Check output names against `output_materializers`, downstream unpacking, and `Annotated` names.
4. Disable cache while validating step body and hook behavior.
5. Confirm settings keys: `docker`, `resources`, component category, component flavor, or component name.
6. For dynamic pipelines, check `.load()` vs `.chunk()`, mapped input lengths, `unmapped(...)`, and child call order.
7. For Docker/remote runs, confirm every optional integration, custom materializer module, and source file is present in the image.
8. For schedules or remote execution, verify active stack support; route stack fixes to `../stacks-and-integrations/SKILL.md`.
