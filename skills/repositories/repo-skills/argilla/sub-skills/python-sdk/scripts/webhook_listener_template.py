#!/usr/bin/env python3
"""Dry-run-safe Argilla webhook listener template.

Default behavior prints guidance. It does not create an Argilla client, register
webhooks, delete webhooks, or start a long-running server unless explicit CLI
flags are provided.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import os
from typing import Any, Dict, Iterable, List, Optional

try:
    from fastapi import FastAPI
except Exception:  # pragma: no cover - template should still show --help without FastAPI
    FastAPI = None  # type: ignore

if FastAPI is not None:
    server = FastAPI(title="Argilla webhook listener template")
else:  # pragma: no cover
    server = None

SUPPORTED_EVENTS = [
    "dataset.created",
    "dataset.updated",
    "dataset.deleted",
    "dataset.published",
    "record.created",
    "record.updated",
    "record.deleted",
    "record.completed",
    "response.created",
    "response.updated",
    "response.deleted",
]

DEFAULT_EVENTS = ["record.completed", "response.created"]


def _ensure_server():
    if server is None:
        raise RuntimeError("FastAPI is required to build the webhook ASGI server. Install fastapi and uvicorn first.")
    return server


def _group_events(events: Iterable[str]) -> Dict[str, List[str]]:
    grouped: Dict[str, List[str]] = {"dataset": [], "record": [], "response": []}
    for event in events:
        if event not in SUPPORTED_EVENTS:
            raise ValueError(f"Unsupported event {event!r}. Choose from: {', '.join(SUPPORTED_EVENTS)}")
        grouped[event.split(".", 1)[0]].append(event)
    return grouped


def build_client(args):
    """Create a live Argilla client only when --register is explicitly supplied."""
    import argilla as rg

    http_client_args = {}
    if args.hf_token:
        http_client_args["headers"] = {"Authorization": f"Bearer {args.hf_token}"}

    return rg.Argilla(
        api_url=args.api_url,
        api_key=args.api_key,
        timeout=args.timeout,
        retries=args.retries,
        **http_client_args,
    )


def register_listeners(client: Any, events: Iterable[str], raw_event: bool = False) -> None:
    """Register event handlers and create FastAPI endpoints.

    This function mutates the live Argilla server by creating/updating webhook
    resources through rg.webhook_listener. It is never called by default.
    """
    import argilla as rg

    app = _ensure_server()
    grouped = _group_events(events)

    if grouped["record"]:
        @rg.webhook_listener(
            events=grouped["record"],
            description="Template listener for Argilla record events",
            client=client,
            server=app,
            raw_event=raw_event,
        )
        async def record_event_listener(*args: Any, **kwargs: Any):
            if raw_event:
                event = args[0] if args else None
                print("raw record event", event)
                return {"ok": True}
            record = kwargs.get("record")
            event_type = kwargs.get("type")
            timestamp: Optional[datetime] = kwargs.get("timestamp")
            print(f"record event={event_type} timestamp={timestamp} record={record}")
            return {"ok": True}

    if grouped["response"]:
        @rg.webhook_listener(
            events=grouped["response"],
            description="Template listener for Argilla response events",
            client=client,
            server=app,
            raw_event=raw_event,
        )
        async def response_event_listener(*args: Any, **kwargs: Any):
            if raw_event:
                event = args[0] if args else None
                print("raw response event", event)
                return {"ok": True}
            response = kwargs.get("response")
            event_type = kwargs.get("type")
            timestamp: Optional[datetime] = kwargs.get("timestamp")
            print(f"response event={event_type} timestamp={timestamp} response={response}")
            return {"ok": True}

    if grouped["dataset"]:
        @rg.webhook_listener(
            events=grouped["dataset"],
            description="Template listener for Argilla dataset events",
            client=client,
            server=app,
            raw_event=raw_event,
        )
        async def dataset_event_listener(*args: Any, **kwargs: Any):
            if raw_event:
                event = args[0] if args else None
                print("raw dataset event", event)
                return {"ok": True}
            dataset = kwargs.get("dataset")
            event_type = kwargs.get("type")
            timestamp: Optional[datetime] = kwargs.get("timestamp")
            print(f"dataset event={event_type} timestamp={timestamp} dataset={dataset}")
            return {"ok": True}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Safe Argilla webhook listener template. No registration or server start occurs by default.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--list-events", action="store_true", help="Print supported Argilla event names and exit")
    parser.add_argument("--event", action="append", dest="events", help="Event to register; can be repeated")
    parser.add_argument("--raw-event", action="store_true", help="Pass the raw verified webhook event object to handlers")
    parser.add_argument("--register", action="store_true", help="Create/update live Argilla webhook resources for selected events")
    parser.add_argument("--serve", action="store_true", help="Start uvicorn with the template FastAPI server")
    parser.add_argument("--host", default="0.0.0.0", help="Host for --serve")
    parser.add_argument("--port", type=int, default=8000, help="Port for --serve")
    parser.add_argument("--api-url", default=os.getenv("ARGILLA_API_URL", "http://localhost:6900"))
    parser.add_argument("--api-key", default=os.getenv("ARGILLA_API_KEY"))
    parser.add_argument("--hf-token", default=os.getenv("HF_TOKEN"), help="Optional HF token for private Spaces header")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--retries", type=int, default=5)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    selected_events = args.events or DEFAULT_EVENTS

    if args.list_events:
        print("\n".join(SUPPORTED_EVENTS))
        return 0

    if not args.register and not args.serve:
        print("Dry run only. No Argilla client was created, no webhooks were registered/deleted, and no server was started.")
        print(f"Template FastAPI server object: {'available as webhook_listener_template:server' if server is not None else 'FastAPI not installed'}")
        print(f"Default events if registering: {', '.join(DEFAULT_EVENTS)}")
        print("Set WEBHOOK_SERVER_URL to the public URL reachable by Argilla before registering live webhooks.")
        print("Use --register to intentionally create/update webhooks and --serve to intentionally start uvicorn.")
        return 0

    if args.register:
        if not args.api_key:
            raise SystemExit("--register requires --api-key or ARGILLA_API_KEY")
        client = build_client(args)
        register_listeners(client=client, events=selected_events, raw_event=args.raw_event)
        print(f"Registered listener endpoints for: {', '.join(selected_events)}")

    if args.serve:
        app = _ensure_server()
        import uvicorn

        print(f"Starting webhook server on {args.host}:{args.port}. Stop with Ctrl+C.")
        uvicorn.run(app, host=args.host, port=args.port)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
