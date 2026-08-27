#!/usr/bin/env python3
"""Build and redact Viseron-style FFmpeg/GStreamer camera URLs.

This helper is intentionally offline: it validates and formats URL strings only.
It never opens sockets, invokes FFmpeg/FFprobe, reads config files, or contacts a
camera. It mirrors Viseron's stream URL model closely enough for configuration
review while keeping credentials redacted by default.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import quote

FORMAT_TO_PROTOCOL = {
    "rtsp": "rtsp",
    "rtmp": "rtmp",
    "mjpeg": "http",
}
PROTOCOL_CHOICES = ("rtsp", "rtsps", "rtmp", "http", "https")
STREAM_FORMAT_CHOICES = tuple(FORMAT_TO_PROTOCOL)


@dataclass(frozen=True)
class BuiltURL:
    """Rendered stream URL variants."""

    label: str
    stream_format: str
    protocol: str
    url: str
    redacted_url: str


def positive_port(value: str) -> int:
    """Validate a TCP/UDP port number."""
    try:
        port = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def normalize_host(host: str) -> str:
    """Reject values that look like full URLs instead of hostnames/IPs."""
    host = host.strip()
    if not host:
        raise argparse.ArgumentTypeError("host cannot be empty")
    if "://" in host or "/" in host:
        raise argparse.ArgumentTypeError(
            "host should be only a hostname or IP address, not a full URL"
        )
    return host


def normalize_path(path: str) -> str:
    """Normalize a camera path while rejecting full-URL injection mistakes."""
    path = path.strip()
    if not path:
        raise argparse.ArgumentTypeError("path cannot be empty")
    if "://" in path:
        raise argparse.ArgumentTypeError(
            "path should be only the URL path, for example /Streaming/Channels/101/"
        )
    # Collapse leading // to / so a pasted protocol-relative URL cannot be emitted.
    if path.startswith("//"):
        path = "/" + path.lstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return path


def resolve_protocol(stream_format: str, protocol: str | None) -> str:
    """Return explicit protocol or the Viseron default for the stream format."""
    return protocol or FORMAT_TO_PROTOCOL[stream_format]


def build_url(
    *,
    label: str,
    host: str,
    port: int,
    path: str,
    stream_format: str,
    protocol: str | None,
    username: str | None,
    password: str | None,
    redact_token: str,
) -> BuiltURL:
    """Build raw and redacted URL variants."""
    resolved_protocol = resolve_protocol(stream_format, protocol)
    auth = ""
    redacted_auth = ""
    if username is not None and password is not None:
        auth = f"{username}:{quote(password, safe='')}@"
        redacted_auth = f"{redact_token}:{redact_token}@"

    suffix = f"{host}:{port}{path}"
    return BuiltURL(
        label=label,
        stream_format=stream_format,
        protocol=resolved_protocol,
        url=f"{resolved_protocol}://{auth}{suffix}",
        redacted_url=f"{resolved_protocol}://{redacted_auth}{suffix}",
    )


def parser() -> argparse.ArgumentParser:
    """Create CLI parser."""
    p = argparse.ArgumentParser(
        description=(
            "Build Viseron-style RTSP/RTMP/MJPEG camera URLs and redact "
            "credentials without contacting the camera."
        )
    )
    p.add_argument("--host", required=True, type=normalize_host, help="Camera host/IP.")
    p.add_argument("--port", required=True, type=positive_port, help="Camera port.")
    p.add_argument(
        "--path",
        required=True,
        type=normalize_path,
        help="Camera URL path, e.g. /Streaming/Channels/101/.",
    )
    p.add_argument(
        "--stream-format",
        choices=STREAM_FORMAT_CHOICES,
        default="rtsp",
        help="Viseron stream_format; defaults to rtsp.",
    )
    p.add_argument(
        "--protocol",
        choices=PROTOCOL_CHOICES,
        default=None,
        help="Optional protocol override such as rtsps or https.",
    )
    p.add_argument("--username", help="Camera username. Requires --password.")
    p.add_argument("--password", help="Camera password. Requires --username.")
    p.add_argument(
        "--redact-token",
        default="*****",
        help="Replacement token used in redacted URLs.",
    )
    p.add_argument(
        "--show-secret",
        action="store_true",
        help="Also print raw URL with credentials. Off by default.",
    )
    p.add_argument(
        "--substream",
        action="store_true",
        help="Also build a substream URL from --sub-path/--sub-port.",
    )
    p.add_argument("--sub-port", type=positive_port, help="Substream port.")
    p.add_argument("--sub-path", type=normalize_path, help="Substream path.")
    p.add_argument(
        "--sub-stream-format",
        choices=STREAM_FORMAT_CHOICES,
        default=None,
        help="Substream stream_format; defaults to main --stream-format.",
    )
    p.add_argument(
        "--sub-protocol",
        choices=PROTOCOL_CHOICES,
        default=None,
        help="Substream protocol override.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    return p


def validate_args(args: argparse.Namespace, p: argparse.ArgumentParser) -> None:
    """Validate cross-field constraints."""
    if (args.username is None) ^ (args.password is None):
        p.error("--username and --password must be provided together or both omitted")
    if args.substream and (args.sub_port is None or args.sub_path is None):
        p.error("--substream requires --sub-port and --sub-path")
    if not args.substream and any(
        value is not None
        for value in (args.sub_port, args.sub_path, args.sub_stream_format, args.sub_protocol)
    ):
        p.error("substream-specific arguments require --substream")


def build_all(args: argparse.Namespace) -> list[BuiltURL]:
    """Build main and optional substream URL records."""
    urls = [
        build_url(
            label="main",
            host=args.host,
            port=args.port,
            path=args.path,
            stream_format=args.stream_format,
            protocol=args.protocol,
            username=args.username,
            password=args.password,
            redact_token=args.redact_token,
        )
    ]
    if args.substream:
        sub_format = args.sub_stream_format or args.stream_format
        urls.append(
            build_url(
                label="substream",
                host=args.host,
                port=args.sub_port,
                path=args.sub_path,
                stream_format=sub_format,
                protocol=args.sub_protocol,
                username=args.username,
                password=args.password,
                redact_token=args.redact_token,
            )
        )
    return urls


def emit_text(urls: list[BuiltURL], *, show_secret: bool) -> None:
    """Print human-readable output."""
    for item in urls:
        print(f"[{item.label}]")
        print(f"stream_format: {item.stream_format}")
        print(f"protocol: {item.protocol}")
        print(f"redacted_url: {item.redacted_url}")
        if show_secret:
            print(f"url: {item.url}")
        print()


def emit_json(urls: list[BuiltURL], *, show_secret: bool) -> None:
    """Print JSON output, hiding raw URL unless requested."""
    records: list[dict[str, Any]] = []
    for item in urls:
        record = asdict(item)
        if not show_secret:
            record.pop("url")
        records.append(record)
    print(json.dumps({"urls": records}, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    p = parser()
    args = p.parse_args(argv)
    validate_args(args, p)
    urls = build_all(args)
    if args.json:
        emit_json(urls, show_secret=args.show_secret)
    else:
        emit_text(urls, show_secret=args.show_secret)
    return 0


if __name__ == "__main__":
    sys.exit(main())
