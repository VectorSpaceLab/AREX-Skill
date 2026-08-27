#!/usr/bin/env python3
"""Non-mutating cuML source-build prerequisite probe.

The probe checks host/toolchain readiness for source builds and CUDA runtime
validation. It does not configure, compile, install packages, import cuML, or
write files.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


MIN_CUDA = (12, 2)
MIN_GCC = (13, 0)
MIN_CMAKE = (4, 0)
MIN_PYTHON = (3, 11)
MAX_PYTHON = (3, 14)
MIN_CYTHON = (3, 2, 2)
CUDA_CC_MIN = {12: 7.0, 13: 7.5}


@dataclass
class Check:
    name: str
    status: str
    message: str
    severity: str = "info"
    details: Optional[Dict[str, object]] = None


def run_command(cmd: Sequence[str], timeout: float) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            list(cmd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return 127, "", "command not found"
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout if isinstance(exc.stdout, str) else ""
        err = exc.stderr if isinstance(exc.stderr, str) else ""
        return 124, out, err or "command timed out"
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def parse_version_tuple(text: str) -> Optional[Tuple[int, ...]]:
    match = re.search(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", text)
    if not match:
        return None
    parts = [int(p) for p in match.groups() if p is not None]
    return tuple(parts)


def version_ge(found: Optional[Tuple[int, ...]], required: Tuple[int, ...]) -> bool:
    if found is None:
        return False
    width = max(len(found), len(required))
    a = found + (0,) * (width - len(found))
    b = required + (0,) * (width - len(required))
    return a >= b


def version_le(found: Optional[Tuple[int, ...]], maximum: Tuple[int, ...]) -> bool:
    if found is None:
        return False
    width = max(len(found), len(maximum))
    a = found + (0,) * (width - len(found))
    b = maximum + (99,) * (width - len(maximum))
    return a <= b


def fmt_version(v: Optional[Tuple[int, ...]]) -> str:
    return ".".join(str(x) for x in v) if v is not None else "unknown"


def command_available(command: str) -> bool:
    return shutil.which(command) is not None


def add_tool_check(
    checks: List[Check],
    command: str,
    version_cmd: Sequence[str],
    min_version: Optional[Tuple[int, ...]],
    timeout: float,
    parse_from: str = "stdout",
    required: bool = True,
    version_regex: Optional[str] = None,
) -> Optional[Tuple[int, ...]]:
    if not command_available(command):
        checks.append(
            Check(
                name=command,
                status="fail" if required else "warn",
                severity="required" if required else "optional",
                message=f"{command} is not available on PATH",
            )
        )
        return None

    rc, out, err = run_command(version_cmd, timeout)
    text = out if parse_from == "stdout" else f"{out}\n{err}"
    if rc != 0 and not text.strip():
        checks.append(
            Check(
                name=command,
                status="fail" if required else "warn",
                severity="required" if required else "optional",
                message=f"{command} exists but version command failed with exit {rc}",
            )
        )
        return None

    if version_regex:
        match = re.search(version_regex, text)
        version = parse_version_tuple(match.group(1)) if match else parse_version_tuple(text)
    else:
        version = parse_version_tuple(text)

    if min_version is None:
        checks.append(
            Check(
                name=command,
                status="pass",
                message=f"{command} is available",
                details={"version": fmt_version(version)},
            )
        )
        return version

    ok = version_ge(version, min_version)
    checks.append(
        Check(
            name=command,
            status="pass" if ok else "fail",
            severity="required" if required else "optional",
            message=(
                f"{command} version {fmt_version(version)} satisfies >= {fmt_version(min_version)}"
                if ok
                else f"{command} version {fmt_version(version)} is below required >= {fmt_version(min_version)}"
            ),
            details={"version": fmt_version(version), "required_min": fmt_version(min_version)},
        )
    )
    return version


def probe_python(checks: List[Check]) -> None:
    found = sys.version_info[:3]
    ok = version_ge(found, MIN_PYTHON) and version_le(found, MAX_PYTHON)
    checks.append(
        Check(
            name="python",
            status="pass" if ok else "fail",
            severity="required",
            message=(
                f"Python {fmt_version(found)} is within supported range "
                f">= {fmt_version(MIN_PYTHON)} and <= {fmt_version(MAX_PYTHON)}"
                if ok
                else f"Python {fmt_version(found)} is outside supported range "
                f">= {fmt_version(MIN_PYTHON)} and <= {fmt_version(MAX_PYTHON)}"
            ),
            details={"version": fmt_version(found)},
        )
    )


def probe_cython(checks: List[Check]) -> None:
    try:
        import Cython  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on environment
        checks.append(
            Check(
                name="cython",
                status="fail",
                severity="required",
                message=f"Cython is not importable by this Python: {exc.__class__.__name__}",
            )
        )
        return
    version = parse_version_tuple(getattr(Cython, "__version__", ""))
    ok = version_ge(version, MIN_CYTHON) and version != (3, 2, 7)
    message = (
        f"Cython {fmt_version(version)} satisfies >= {fmt_version(MIN_CYTHON)}"
        if ok
        else f"Cython {fmt_version(version)} is below required >= {fmt_version(MIN_CYTHON)} or is excluded"
    )
    checks.append(
        Check(
            name="cython",
            status="pass" if ok else "fail",
            severity="required",
            message=message,
            details={"version": fmt_version(version), "required_min": fmt_version(MIN_CYTHON)},
        )
    )


def parse_gpu_rows(text: str) -> List[Dict[str, object]]:
    gpus: List[Dict[str, object]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 4:
            continue
        index, name, cc_text, driver = parts[:4]
        try:
            cc = float(cc_text)
        except ValueError:
            cc = None
        gpus.append({"index": index, "name": name, "compute_capability": cc, "driver": driver})
    return gpus


def probe_gpu(checks: List[Check], timeout: float, target_cuda_major: Optional[int], require_gpu: bool) -> None:
    if not command_available("nvidia-smi"):
        checks.append(
            Check(
                name="nvidia-smi",
                status="fail" if require_gpu else "warn",
                severity="required" if require_gpu else "runtime",
                message="nvidia-smi is not available; source compilation may still work, but CUDA runtime tests cannot be validated",
            )
        )
        return

    query = [
        "nvidia-smi",
        "--query-gpu=index,name,compute_cap,driver_version",
        "--format=csv,noheader,nounits",
    ]
    rc, out, err = run_command(query, timeout)
    if rc != 0:
        checks.append(
            Check(
                name="nvidia-smi",
                status="fail" if require_gpu else "warn",
                severity="required" if require_gpu else "runtime",
                message=f"nvidia-smi query failed with exit {rc}; CUDA runtime tests cannot be validated",
                details={"stderr": err[:240] if err else ""},
            )
        )
        return

    gpus = parse_gpu_rows(out)
    if not gpus:
        checks.append(
            Check(
                name="gpu",
                status="fail" if require_gpu else "warn",
                severity="required" if require_gpu else "runtime",
                message="No NVIDIA GPUs were reported; build may compile, but cuML execution/tests require a GPU",
            )
        )
        return

    details: Dict[str, object] = {"gpu_count": len(gpus), "gpus": gpus}
    if target_cuda_major in CUDA_CC_MIN:
        threshold = CUDA_CC_MIN[target_cuda_major]
        supported = [g for g in gpus if isinstance(g.get("compute_capability"), float) and g["compute_capability"] >= threshold]
        ok = bool(supported)
        checks.append(
            Check(
                name="gpu_compute_capability",
                status="pass" if ok else ("fail" if require_gpu else "warn"),
                severity="required" if require_gpu else "runtime",
                message=(
                    f"At least one GPU satisfies CUDA {target_cuda_major} compute capability >= {threshold}"
                    if ok
                    else f"No visible GPU satisfies CUDA {target_cuda_major} compute capability >= {threshold}"
                ),
                details=details,
            )
        )
    else:
        hints = {
            "cuda12_min_compute_capability": CUDA_CC_MIN[12],
            "cuda13_min_compute_capability": CUDA_CC_MIN[13],
        }
        details.update(hints)
        checks.append(
            Check(
                name="gpu_compute_capability",
                status="pass",
                severity="runtime",
                message=(
                    f"{len(gpus)} NVIDIA GPU(s) visible; compare compute capability against CUDA 12/13 thresholds"
                ),
                details=details,
            )
        )


def choose_target_cuda_major(cli_value: str, nvcc_version: Optional[Tuple[int, ...]]) -> Optional[int]:
    if cli_value == "auto":
        if nvcc_version:
            return nvcc_version[0]
        return None
    return int(cli_value)


def summarize(checks: Iterable[Check]) -> str:
    statuses = [c.status for c in checks]
    if any(s == "fail" for s in statuses):
        return "fail"
    if any(s == "warn" for s in statuses):
        return "warn"
    return "pass"


def render_text(payload: Dict[str, object]) -> str:
    lines = ["cuML source-build prerequisite probe", f"overall: {payload['overall']}", ""]
    for item in payload["checks"]:  # type: ignore[index]
        check = item if isinstance(item, dict) else asdict(item)
        status = str(check["status"]).upper()
        lines.append(f"[{status}] {check['name']}: {check['message']}")
        details = check.get("details")
        if isinstance(details, dict):
            for key, value in details.items():
                if key == "gpus" and isinstance(value, list):
                    for gpu in value:
                        if isinstance(gpu, dict):
                            lines.append(
                                "  - gpu {index}: {name}, cc={cc}, driver={driver}".format(
                                    index=gpu.get("index", "?"),
                                    name=gpu.get("name", "unknown"),
                                    cc=gpu.get("compute_capability", "unknown"),
                                    driver=gpu.get("driver", "unknown"),
                                )
                            )
                else:
                    lines.append(f"  - {key}: {value}")
    lines.append("")
    lines.append("notes:")
    lines.append("  - This probe is read-only; it does not configure, build, install, or import cuML.")
    lines.append("  - GPU support thresholds: CUDA 12 requires cc >= 7.0; CUDA 13 requires cc >= 7.5.")
    lines.append("  - Source builds require matching CUDA/RAPIDS dependency variants in the active environment.")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check host/toolchain prerequisites for cuML source builds without building anything."
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Default: text.",
    )
    parser.add_argument(
        "--target-cuda-major",
        choices=("auto", "12", "13"),
        default="auto",
        help="CUDA major version to use for compute-capability checks. Default: infer from nvcc when available.",
    )
    parser.add_argument(
        "--require-gpu",
        action="store_true",
        help="Treat missing/unsupported GPU as a failure instead of a runtime warning.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero when required build prerequisites fail.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Timeout in seconds for each external command. Default: 5.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    checks: List[Check] = []

    probe_python(checks)
    probe_cython(checks)

    probe_gpu(checks, args.timeout, None if args.target_cuda_major == "auto" else int(args.target_cuda_major), args.require_gpu)

    nvcc_version = add_tool_check(
        checks,
        "nvcc",
        ("nvcc", "--version"),
        MIN_CUDA,
        args.timeout,
        parse_from="both",
        version_regex=r"release\s+([0-9]+(?:\.[0-9]+)*)",
    )
    target_cuda_major = choose_target_cuda_major(args.target_cuda_major, nvcc_version)
    if args.target_cuda_major == "auto" and target_cuda_major in CUDA_CC_MIN:
        # Add an explicit compute capability interpretation for the detected compiler major.
        probe_gpu(checks, args.timeout, target_cuda_major, args.require_gpu)

    add_tool_check(checks, "gcc", ("gcc", "-dumpfullversion", "-dumpversion"), MIN_GCC, args.timeout)
    add_tool_check(checks, "g++", ("g++", "-dumpfullversion", "-dumpversion"), MIN_GCC, args.timeout)
    add_tool_check(checks, "cmake", ("cmake", "--version"), MIN_CMAKE, args.timeout)
    add_tool_check(checks, "ninja", ("ninja", "--version"), None, args.timeout)

    payload: Dict[str, object] = {
        "overall": summarize(checks),
        "checks": [asdict(c) for c in checks],
        "readOnly": True,
        "cudaComputeCapabilityMinimums": {"12": CUDA_CC_MIN[12], "13": CUDA_CC_MIN[13]},
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(render_text(payload))

    if args.strict and any(c.status == "fail" and c.severity == "required" for c in checks):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
