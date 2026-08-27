#!/usr/bin/env python3
"""Generate safe ClearML pipeline skeletons without importing ClearML."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


DECORATOR_TEMPLATE = '''"""ClearML PipelineDecorator skeleton.

Debug locally first, then switch to remote queues after confirming ClearML
credentials, a server, and agents are configured.
"""

from clearml import TaskTypes
from clearml.automation import PipelineDecorator


@PipelineDecorator.component(
    name="preprocess",
    return_values=["processed_data"],
    task_type=TaskTypes.data_processing,
    execution_queue={queue_repr},
)
def preprocess(raw_uri: str):
    # Put step-specific imports here so remote workers capture dependencies.
    return {{"raw_uri": raw_uri}}


@PipelineDecorator.component(
    name="train",
    return_values=["model"],
    task_type=TaskTypes.training,
    execution_queue={queue_repr},
)
def train(processed_data, learning_rate: float = 0.01):
    return {{"processed_data": processed_data, "learning_rate": learning_rate}}


@PipelineDecorator.component(
    name="evaluate",
    return_values=["metrics"],
    task_type=TaskTypes.qc,
    execution_queue={queue_repr},
)
def evaluate(model):
    return {{"score": 0.0, "model": model}}


@PipelineDecorator.pipeline(
    name={name_repr},
    project={project_repr},
    version="0.1.0",
    default_queue={queue_repr},
    pipeline_execution_queue="services",
)
def pipeline(raw_uri: str = "input-reference", learning_rate: float = 0.01):
    processed_data = preprocess(raw_uri)
    model = train(processed_data, learning_rate=learning_rate)
    metrics = evaluate(model)
    print("metrics", metrics)


if __name__ == "__main__":
    # Pick one local debug mode before remote execution.
    # PipelineDecorator.debug_pipeline()
    # PipelineDecorator.run_locally()
    pipeline()
'''


CONTROLLER_TEMPLATE = '''"""ClearML PipelineController skeleton.

Debug locally first, then switch to remote queues after confirming ClearML
credentials, a server, and agents are configured.
"""

from clearml import TaskTypes
from clearml.automation import PipelineController


def preprocess(raw_uri: str):
    # Put step-specific imports here so remote workers capture dependencies.
    return {{"raw_uri": raw_uri}}


def train(processed_data, learning_rate: float):
    return {{"processed_data": processed_data, "learning_rate": learning_rate}}


def evaluate(model):
    return {{"score": 0.0, "model": model}}


def build_pipeline() -> PipelineController:
    pipe = PipelineController(
        project={project_repr},
        name={name_repr},
        version="0.1.0",
        abort_on_failure=True,
        add_pipeline_tags=False,
    )
    pipe.set_default_execution_queue({queue_repr})
    pipe.add_parameter(name="raw_uri", default="input-reference", description="Input data reference")
    pipe.add_parameter(name="learning_rate", default=0.01, description="Training learning rate")
    pipe.add_function_step(
        name="preprocess",
        function=preprocess,
        function_kwargs={{"raw_uri": "${{pipeline.raw_uri}}"}},
        function_return=["processed_data"],
        task_type=TaskTypes.data_processing,
        cache_executed_step=False,
    )
    pipe.add_function_step(
        name="train",
        function=train,
        function_kwargs={{
            "processed_data": "${{preprocess.processed_data}}",
            "learning_rate": "${{pipeline.learning_rate}}",
        }},
        function_return=["model"],
        task_type=TaskTypes.training,
        parents=["preprocess"],
    )
    pipe.add_function_step(
        name="evaluate",
        function=evaluate,
        function_kwargs={{"model": "${{train.model}}"}},
        function_return=["metrics"],
        task_type=TaskTypes.qc,
        parents=["train"],
    )
    return pipe


if __name__ == "__main__":
    pipeline = build_pipeline()
    # Development: pipeline.start_locally(run_pipeline_steps_locally=False)
    # Full local subprocess debug: pipeline.start_locally(run_pipeline_steps_locally=True)
    # Remote controller: pipeline.start(queue="services", wait=True)
    print("Pipeline skeleton built. Uncomment a start mode when ready.")
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write or print a minimal ClearML automation pipeline skeleton without importing ClearML."
    )
    parser.add_argument(
        "--style",
        choices=("decorator", "controller"),
        required=True,
        help="Generate a PipelineDecorator or PipelineController skeleton.",
    )
    parser.add_argument("--project", required=True, help="ClearML project name to embed in the skeleton.")
    parser.add_argument("--name", required=True, help="ClearML pipeline name to embed in the skeleton.")
    parser.add_argument("--queue", required=True, help="Default execution queue for pipeline steps.")
    parser.add_argument("--output", help="Optional output path. Prints to stdout when omitted.")
    return parser.parse_args()


def render_template(style: str, project: str, name: str, queue: str) -> str:
    values = {
        "project_repr": repr(project),
        "name_repr": repr(name),
        "queue_repr": repr(queue),
    }
    template = DECORATOR_TEMPLATE if style == "decorator" else CONTROLLER_TEMPLATE
    return template.format(**values)


def write_output(content: str, output: str | None) -> None:
    if not output:
        sys.stdout.write(content)
        return
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Wrote {path}")


def main() -> int:
    args = parse_args()
    content = render_template(args.style, args.project, args.name, args.queue)
    write_output(content, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
