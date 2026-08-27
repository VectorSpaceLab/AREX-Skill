#!/usr/bin/env python3
"""Read and validate one RealSense TCP RGB-D frame without robot access."""

import argparse
import array
import json
import math
import socket
import struct
import sys


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 50000
DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720
DEFAULT_TIMEOUT = 5.0
TRAILING_PROBE_TIMEOUT = 0.05
PING = b"asdf"


def _read_exact(sock, size):
    chunks = []
    remaining = size
    while remaining:
        chunk = sock.recv(min(1024 * 1024, remaining))
        if not chunk:
            raise RuntimeError(
                "camera closed the connection after %d/%d bytes"
                % (size - remaining, size)
            )
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _probe_trailing_byte(sock, timeout=TRAILING_PROBE_TIMEOUT):
    """Probe once for a byte after the expected frame without waiting long.

    Returns ``eof`` when the peer closes, ``timeout`` when no byte is observed
    within the bounded probe, and ``trailing-byte`` when extra payload exists.
    A timeout is deliberately not treated as proof of exact framing: the
    historical service can keep the TCP connection open after its response.
    """
    probe_timeout = min(TRAILING_PROBE_TIMEOUT, timeout)
    sock.settimeout(probe_timeout)
    try:
        return "trailing-byte" if sock.recv(1) else "eof"
    except socket.timeout:
        return "timeout"
    except OSError as exc:
        raise RuntimeError("trailing-byte probe failed: %s" % exc) from exc


def _decode_depth(raw, byte_order):
    values = array.array("H")
    values.frombytes(raw)
    host_little = struct.pack("=H", 1) == struct.pack("<H", 1)
    requested_little = byte_order == "little"
    if host_little != requested_little:
        values.byteswap()
    return values


def read_frame(
    host,
    port,
    width,
    height,
    timeout,
    byte_order,
    compatibility_dimensions=False,
):
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    if (width, height) != (DEFAULT_WIDTH, DEFAULT_HEIGHT):
        if not compatibility_dimensions:
            raise ValueError(
                "historical protocol validation requires 1280x720; "
                "pass --compatibility-dimensions only for an explicit "
                "non-historical compatibility check"
            )
    if not (0 < port < 65536):
        raise ValueError("port must be in the range 1..65535")
    if timeout <= 0 or not math.isfinite(timeout):
        raise ValueError("timeout must be a finite positive number")
    if byte_order not in ("little", "big"):
        raise ValueError("byte_order must be little or big")

    historical_dimensions = (width, height) == (DEFAULT_WIDTH, DEFAULT_HEIGHT)
    intrinsics_bytes = 9 * 4
    scale_bytes = 4
    depth_bytes = width * height * 2
    color_bytes = width * height * 3
    expected = intrinsics_bytes + scale_bytes + depth_bytes + color_bytes
    float_prefix = "<" if byte_order == "little" else ">"

    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(PING)
            payload = _read_exact(sock, expected)
            trailing_probe = _probe_trailing_byte(sock)
            if trailing_probe == "trailing-byte":
                raise RuntimeError(
                    "unexpected trailing byte after %d-byte frame; "
                    "exact-frame validation rejected the response" % expected
                )
    except OSError as exc:
        raise RuntimeError("camera TCP read failed: %s" % exc) from exc

    intrinsics = struct.unpack(float_prefix + "9f", payload[:intrinsics_bytes])
    depth_scale = struct.unpack(
        float_prefix + "f", payload[intrinsics_bytes:intrinsics_bytes + scale_bytes]
    )[0]
    if not all(math.isfinite(value) for value in intrinsics):
        raise RuntimeError("intrinsics contain a non-finite value")
    if intrinsics[0] <= 0 or intrinsics[4] <= 0:
        raise RuntimeError("intrinsics fx and fy must be positive")
    if not math.isfinite(depth_scale) or depth_scale <= 0:
        raise RuntimeError("depth scale must be finite and positive")

    depth_start = intrinsics_bytes + scale_bytes
    depth_raw = payload[depth_start:depth_start + depth_bytes]
    color_raw = payload[depth_start + depth_bytes:]
    if len(depth_raw) != depth_bytes or len(color_raw) != color_bytes:
        raise RuntimeError("payload component sizes do not match configured dimensions")

    depth_values = _decode_depth(depth_raw, byte_order)
    zero_count = sum(value == 0 for value in depth_values)
    raw_min = min(depth_values) if depth_values else 0
    raw_max = max(depth_values) if depth_values else 0
    color_min = min(color_raw) if color_raw else 0
    color_max = max(color_raw) if color_raw else 0

    return {
        "host": host,
        "port": port,
        "width": width,
        "height": height,
        "dimension_mode": "historical" if historical_dimensions else "compatibility",
        "historical_protocol_validation": historical_dimensions,
        "payload_bytes": len(payload),
        "expected_bytes": expected,
        "trailing_probe": trailing_probe,
        "trailing_probe_timeout_seconds": TRAILING_PROBE_TIMEOUT,
        "exact_frame": trailing_probe == "eof",
        "intrinsics": [list(intrinsics[0:3]), list(intrinsics[3:6]), list(intrinsics[6:9])],
        "depth_scale": depth_scale,
        "depth_raw_min": raw_min,
        "depth_raw_max": raw_max,
        "depth_zero_count": zero_count,
        "depth_value_count": len(depth_values),
        "rgb_min": color_min,
        "rgb_max": color_max,
        "wire_byte_order": byte_order,
    }


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Read one RealSense RGB-D payload using the historical fixed "
            "1280x720 protocol. The bounded trailing-byte probe rejects an "
            "observed extra byte; a probe timeout is reported as inconclusive. "
            "This connects only to the camera TCP service and never accesses a robot."
        )
    )
    parser.add_argument(
        "--host", default=DEFAULT_HOST,
        help="camera server host (default: %(default)s)",
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT,
        help="camera server TCP port (default: %(default)s)",
    )
    parser.add_argument(
        "--width", type=int, default=DEFAULT_WIDTH,
        help="historical fixed width (default: %(default)s)",
    )
    parser.add_argument(
        "--height", type=int, default=DEFAULT_HEIGHT,
        help="historical fixed height (default: %(default)s)",
    )
    parser.add_argument(
        "--compatibility-dimensions", action="store_true",
        help=(
            "allow non-1280x720 dimensions for synthetic/adaptor checks; "
            "this is not validation of the historical protocol"
        ),
    )
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT,
        help="connect/read timeout in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--byte-order", choices=("little", "big"), default="little",
        help="raw float/uint16 byte order; historical deployment is normally little-endian",
    )
    parser.add_argument("--json", action="store_true", help="emit the validation report as JSON")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        report = read_frame(
            args.host,
            args.port,
            args.width,
            args.height,
            args.timeout,
            args.byte_order,
            compatibility_dimensions=args.compatibility_dimensions,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print("capture_rgbd: ERROR: %s" % exc, file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print(
            "RGB-D payload valid: %dx%d, %d/%d bytes (%s dimensions)"
            % (
                report["width"],
                report["height"],
                report["payload_bytes"],
                report["expected_bytes"],
                report["dimension_mode"],
            )
        )
        if report["historical_protocol_validation"]:
            print("historical protocol dimensions: validated (1280x720)")
        else:
            print(
                "WARNING: compatibility dimensions were requested; "
                "this is not historical 1280x720 protocol validation"
            )
        if report["exact_frame"]:
            print("exact-frame probe: peer closed after the expected payload")
        else:
            print(
                "WARNING: no trailing byte observed within %.2fs; exact-frame "
                "validation is inconclusive while the peer remains open"
                % report["trailing_probe_timeout_seconds"]
            )
        print("intrinsics=%s" % report["intrinsics"])
        print(
            "depth_scale=%g raw_depth=[%d,%d] zero=%d/%d"
            % (
                report["depth_scale"],
                report["depth_raw_min"],
                report["depth_raw_max"],
                report["depth_zero_count"],
                report["depth_value_count"],
            )
        )
        print(
            "rgb=[%d,%d] byte_order=%s"
            % (report["rgb_min"], report["rgb_max"], report["wire_byte_order"])
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
