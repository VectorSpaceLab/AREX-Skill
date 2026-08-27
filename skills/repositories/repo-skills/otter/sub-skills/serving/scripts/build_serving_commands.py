#!/usr/bin/env python3
"""Print safe Otter serving command templates without launching services.

The commands target an Otter checkout or deployment that contains the serving
modules. This helper does not import Otter, start servers, open ports, or load
model weights.
"""

from __future__ import annotations

import argparse
import shlex
from dataclasses import dataclass


@dataclass
class ServingPlan:
    checkpoint: str
    model_name: str
    controller_host: str
    controller_port: int
    worker_host: str
    worker_port: int
    gradio_host: str
    gradio_port: int
    num_gpus: int
    load_bit: str
    video: bool
    dispatch_method: str
    concurrency: int
    limit_model_concurrency: int
    share: bool
    moderate: bool

    @property
    def controller_url(self) -> str:
        host_for_url = "localhost" if self.controller_host in {"0.0.0.0", "::"} else self.controller_host
        return f"http://{host_for_url}:{self.controller_port}"

    @property
    def worker_url(self) -> str:
        host_for_url = "localhost" if self.worker_host in {"0.0.0.0", "::"} else self.worker_host
        return f"http://{host_for_url}:{self.worker_port}"


def q(parts: list[str]) -> str:
    return " ".join(shlex.quote(str(p)) for p in parts)


def build_commands(plan: ServingPlan) -> list[tuple[str, str]]:
    controller = [
        "python",
        "-m",
        "pipeline.serve.controller",
        "--host",
        plan.controller_host,
        "--port",
        str(plan.controller_port),
        "--dispatch-method",
        plan.dispatch_method,
    ]
    worker = [
        "python",
        "-m",
        "pipeline.serve.model_worker",
        "--host",
        plan.worker_host,
        "--port",
        str(plan.worker_port),
        "--worker_address",
        plan.worker_url,
        "--controller_address",
        plan.controller_url,
        "--model_name",
        plan.model_name,
        "--checkpoint_path",
        plan.checkpoint,
        "--num_gpus",
        str(plan.num_gpus),
        "--load_bit",
        plan.load_bit,
        "--limit_model_concurrency",
        str(plan.limit_model_concurrency),
    ]
    gradio_module = "pipeline.serve.gradio_web_server_video" if plan.video else "pipeline.serve.gradio_web_server"
    gradio = [
        "python",
        "-m",
        gradio_module,
        "--host",
        plan.gradio_host,
        "--port",
        str(plan.gradio_port),
        "--controller_url",
        plan.controller_url,
        "--concurrency_count",
        str(plan.concurrency),
    ]
    if plan.share:
        gradio.append("--share")
    if plan.moderate:
        gradio.append("--moderate")
    return [("controller", q(controller)), ("worker", q(worker)), ("gradio", q(gradio))]


def main() -> int:
    parser = argparse.ArgumentParser(description="Print Otter serving command templates without launching services.")
    parser.add_argument("--checkpoint", required=True, help="Otter/Flamingo checkpoint path or Hugging Face model id.")
    parser.add_argument("--model-name", default="otter", help="Model name advertised by the worker/controller.")
    parser.add_argument("--controller-host", default="0.0.0.0")
    parser.add_argument("--controller-port", type=int, default=21001)
    parser.add_argument("--worker-host", default="0.0.0.0")
    parser.add_argument("--worker-port", type=int, default=21002)
    parser.add_argument("--gradio-host", default="127.0.0.1")
    parser.add_argument("--gradio-port", type=int, default=7861)
    parser.add_argument("--num-gpus", type=int, default=1)
    parser.add_argument("--load-bit", choices=["fp16", "bf16", "int8", "int4", "fp32"], default="fp32")
    parser.add_argument("--dispatch-method", choices=["shortest_queue", "lottery"], default="shortest_queue")
    parser.add_argument("--concurrency", type=int, default=16, help="Gradio queue concurrency_count.")
    parser.add_argument("--limit-model-concurrency", type=int, default=5, help="Worker semaphore limit.")
    parser.add_argument("--video", action="store_true", help="Use the video Gradio server module.")
    parser.add_argument("--share", action="store_true", help="Add Gradio --share to the generated UI command.")
    parser.add_argument("--moderate", action="store_true", help="Add Gradio --moderate; requires OPENAI_API_KEY at runtime.")
    args = parser.parse_args()

    if args.controller_port == args.worker_port or args.controller_port == args.gradio_port or args.worker_port == args.gradio_port:
        parser.error("controller, worker, and Gradio ports must be distinct")
    if args.num_gpus < 0:
        parser.error("--num-gpus must be >= 0")

    plan = ServingPlan(
        checkpoint=args.checkpoint,
        model_name=args.model_name,
        controller_host=args.controller_host,
        controller_port=args.controller_port,
        worker_host=args.worker_host,
        worker_port=args.worker_port,
        gradio_host=args.gradio_host,
        gradio_port=args.gradio_port,
        num_gpus=args.num_gpus,
        load_bit=args.load_bit,
        video=args.video,
        dispatch_method=args.dispatch_method,
        concurrency=args.concurrency,
        limit_model_concurrency=args.limit_model_concurrency,
        share=args.share,
        moderate=args.moderate,
    )

    print("# Otter serving command templates")
    print("# Run from a target Otter checkout or deployment that contains pipeline.serve modules.")
    for label, command in build_commands(plan):
        print(f"\n## {label}")
        print(command)
    if args.moderate:
        print("\n# Note: --moderate requires OPENAI_API_KEY at runtime.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
