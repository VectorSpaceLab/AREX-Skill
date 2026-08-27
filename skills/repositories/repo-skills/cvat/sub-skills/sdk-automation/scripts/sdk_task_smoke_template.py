#!/usr/bin/env python3
"""Safe CVAT SDK smoke/template script.

Default mode performs imports and signature inspection without contacting a server.
Authenticated modes require an explicit server/profile/token/password setup and may read
server state; create/upload/delete operations are intentionally not implemented here.
"""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path
from typing import Any

from cvat_sdk import configure_client_auth_arguments, make_client_from_cli


def local_smoke() -> dict[str, Any]:
    from cvat_sdk import Client, Config, make_client
    from cvat_sdk.core.proxies.projects import Project
    from cvat_sdk.core.proxies.tasks import ResourceType, Task
    import cvat_sdk.auto_annotation as cvataa

    return {
        "Client.__init__": str(inspect.signature(Client.__init__)),
        "make_client": str(inspect.signature(make_client)),
        "Task.upload_data": str(inspect.signature(Task.upload_data)),
        "Task.download_frames": str(inspect.signature(Task.download_frames)),
        "Project.import_dataset": str(inspect.signature(Project.import_dataset)),
        "ResourceType": [str(x) for x in ResourceType],
        "Config": str(Config),
        "auto_annotation_helpers": [
            name for name in ("label_spec", "rectangle", "mask", "annotate_task") if hasattr(cvataa, name)
        ],
    }


def list_tasks(args: argparse.Namespace) -> dict[str, Any]:
    with make_client_from_cli(args) as client:
        tasks = client.tasks.list(return_json=args.json_output)
        if args.json_output:
            return {"tasks_json": json.loads(tasks)}
        return {"task_ids": [task.id for task in tasks]}


def download_frames(args: argparse.Namespace) -> dict[str, Any]:
    if not args.frame_ids:
        raise SystemExit("--frame-id is required for download-frames")
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    with make_client_from_cli(args) as client:
        task = client.tasks.retrieve(args.task_id)
        task.download_frames(
            args.frame_ids,
            outdir=outdir,
            quality=args.quality,
            image_extension=args.image_extension,
        )
        return {"downloaded_frames": args.frame_ids, "outdir": str(outdir)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    smoke = sub.add_parser("local-smoke", help="inspect SDK imports/signatures without contacting a server")
    smoke.set_defaults(func=lambda args: local_smoke())

    list_parser = sub.add_parser("list-tasks", help="authenticate and list task ids or JSON")
    configure_client_auth_arguments(list_parser)
    list_parser.add_argument("--json-output", action="store_true", help="request JSON output from the SDK repo list method")
    list_parser.set_defaults(func=list_tasks)

    frames = sub.add_parser("download-frames", help="authenticate and download selected task frames")
    configure_client_auth_arguments(frames)
    frames.add_argument("--task-id", type=int, required=True)
    frames.add_argument("--frame-id", dest="frame_ids", type=int, action="append", default=[])
    frames.add_argument("--outdir", default="frames")
    frames.add_argument("--quality", choices=("original", "compressed"), default="compressed")
    frames.add_argument("--image-extension", help="force extension such as jpg or png")
    frames.set_defaults(func=download_frames)

    args = parser.parse_args()
    print(json.dumps(args.func(args), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
