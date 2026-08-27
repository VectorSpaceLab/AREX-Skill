#!/usr/bin/env python3
"""Safe, non-interactive preflight for AgiBot X1 MuJoCo sim2sim.

This helper never imports ``humanoid`` or ``humanoid.envs``, initializes
pygame, opens a joystick, deserializes TorchScript, creates a MuJoCo viewer, or
steps a simulation.  Its optional MuJoCo check compiles XML in a child process
without creating a viewer.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple
import xml.etree.ElementTree as ET
import zipfile

TASK = "x1_dh_stand"
EXPECTED_MUJOCO = "2.3.6"
ACTIONS = 12
SINGLE_OBS = 47
HISTORY = 66
POLICY_INPUT = SINGLE_OBS * HISTORY
SHORT_HISTORY = 5
POLICY_OUTPUT = 12
EXPECTED_MJCF_JOINTS = [
    "left_hip_pitch",
    "left_hip_roll",
    "left_hip_yaw",
    "left_knee_pitch",
    "left_ankle_pitch",
    "left_ankle_roll",
    "right_hip_pitch",
    "right_hip_roll",
    "right_hip_yaw",
    "right_knee_pitch",
    "right_ankle_pitch",
    "right_ankle_roll",
]
EXPECTED_URDF_JOINTS = [name + "_joint" for name in EXPECTED_MJCF_JOINTS]
EXPECTED_SENSORS = {
    "body-orientation",
    "body-angular-velocity",
    "body-linear-pos",
    "body-linear-vel",
    "body-linear-acceleration",
}
EXPECTED_INCLUDES = {
    "robot/xyber_x1/xyber_x1_serial.xml",
    "environment/flat.xml",
}


class Report:
    def __init__(self) -> None:
        self.checks: List[Dict[str, str]] = []
        self.details: Dict[str, Any] = {
            "task": TASK,
            "shape_contract": {
                "single_observation": SINGLE_OBS,
                "history_frames": HISTORY,
                "policy_input": POLICY_INPUT,
                "short_history_frames": SHORT_HISTORY,
                "actions": ACTIONS,
            },
        }

    def add(self, level: str, code: str, message: str) -> None:
        self.checks.append({"level": level, "code": code, "message": message})

    def ok(self, code: str, message: str) -> None:
        self.add("OK", code, message)

    def warn(self, code: str, message: str) -> None:
        self.add("WARNING", code, message)

    def error(self, code: str, message: str) -> None:
        self.add("ERROR", code, message)

    def blocked(self, code: str, message: str) -> None:
        self.add("BLOCKED_REQUIRED_BACKEND", code, message)

    def has_errors(self) -> bool:
        return any(item["level"] == "ERROR" for item in self.checks)

    def has_blocks(self) -> bool:
        return any(item["level"] == "BLOCKED_REQUIRED_BACKEND" for item in self.checks)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Statically validate the X1 sim2sim task, JIT directory, MJCF "
            "include/mesh graph, URDF joints, and runtime metadata without "
            "opening a viewer or loading policy code."
        )
    )
    parser.add_argument(
        "--task",
        required=True,
        help="Registered task; this helper verifies only x1_dh_stand.",
    )
    parser.add_argument(
        "--asset-root",
        type=Path,
        help=(
            "X1 asset root containing mjcf/xyber_x1_flat.xml, mjcf includes, "
            "meshes/, and urdf/x1.urdf."
        ),
    )
    parser.add_argument(
        "--mjcf-model",
        type=Path,
        help="Explicit top-level MJCF model; overrides --asset-root's default.",
    )
    parser.add_argument(
        "--urdf",
        type=Path,
        help="Explicit X1 URDF; overrides --asset-root's default.",
    )
    parser.add_argument(
        "--logs-root",
        type=Path,
        default=Path("logs"),
        help="Log root used to resolve a relative --load-model (default: logs).",
    )
    parser.add_argument(
        "--load-model",
        type=Path,
        help=(
            "Value intended for native --load_model. It must resolve to one "
            "timestamp directory containing exactly one policy file, not to "
            "the policy file or exported_policies parent."
        ),
    )
    parser.add_argument(
        "--discover-latest-model",
        action="store_true",
        help=(
            "When --load-model is omitted, inspect the lexicographically last "
            "directory below logs/<task>/exported_policies."
        ),
    )
    parser.add_argument(
        "--compile-mujoco",
        action="store_true",
        help=(
            "Also compile MJCF in a child process with installed mujoco. This "
            "does not create a viewer or step simulation."
        ),
    )
    parser.add_argument(
        "--require-runtime",
        action="store_true",
        help=(
            "Treat missing/pin-mismatched runtime modules, display, and "
            "joystick as errors. Without this flag, isolated validation may pass "
            "while full sim2sim remains BLOCKED_REQUIRED_BACKEND."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit one JSON object instead of a human-readable report.",
    )
    return parser


def inside(path: Path, root: Path) -> bool:
    try:
        return os.path.commonpath([str(path), str(root)]) == str(root)
    except ValueError:
        return False


def checked_file(path: Path, boundary: Optional[Path], report: Report, code: str) -> Optional[Path]:
    resolved = path.expanduser().resolve()
    if boundary is not None and not inside(resolved, boundary):
        report.error(code, "path escapes the declared asset root: {}".format(path))
        return None
    if not resolved.is_file():
        report.error(code, "required file is missing: {}".format(path))
        return None
    try:
        if resolved.stat().st_size > 20 * 1024 * 1024:
            report.error(code, "refusing to parse XML larger than 20 MiB: {}".format(path))
            return None
    except OSError as exc:
        report.error(code, "could not stat {}: {}".format(path, exc))
        return None
    return resolved


def parse_xml(path: Path, report: Report, code: str) -> Optional[ET.Element]:
    try:
        return ET.parse(str(path)).getroot()
    except (ET.ParseError, OSError) as exc:
        report.error(code, "XML parse failed for {}: {}".format(path, exc))
        return None


def validate_mjcf(path: Path, boundary: Optional[Path], report: Report) -> None:
    top = checked_file(path, boundary, report, "mjcf-model")
    if top is None:
        return
    top_root = parse_xml(top, report, "mjcf-parse")
    if top_root is None:
        return
    if top_root.tag != "mujoco":
        report.error("mjcf-root", "top-level MJCF root must be <mujoco>")
        return

    documents: List[Tuple[Path, ET.Element]] = [(top, top_root)]
    pending: List[Tuple[Path, ET.Element]] = [(top, top_root)]
    seen = {top}
    include_names: List[str] = []
    while pending:
        current_path, current_root = pending.pop(0)
        for include in current_root.findall(".//include"):
            value = include.get("file")
            if not value:
                report.error("mjcf-include", "an <include> has no file attribute")
                continue
            include_path = (current_path.parent / value).resolve()
            if current_path == top:
                include_names.append(Path(value).as_posix())
            checked = checked_file(include_path, boundary, report, "mjcf-include")
            if checked is None or checked in seen:
                continue
            root = parse_xml(checked, report, "mjcf-include-parse")
            if root is None:
                continue
            seen.add(checked)
            documents.append((checked, root))
            pending.append((checked, root))

    if set(include_names) != EXPECTED_INCLUDES:
        report.error(
            "mjcf-include-contract",
            "top-level includes are {}, expected {}".format(
                sorted(include_names), sorted(EXPECTED_INCLUDES)
            ),
        )
    else:
        report.ok("mjcf-includes", "both robot and flat-environment includes resolve")

    compiler_meshdirs: List[str] = []
    meshes: List[Tuple[str, str]] = []
    actuators: List[Tuple[str, str]] = []
    hinge_joints: List[str] = []
    sensors = set()
    key_qpos_widths: List[int] = []
    for _, root in documents:
        for compiler in root.findall(".//compiler"):
            value = compiler.get("meshdir")
            if value:
                compiler_meshdirs.append(value)
        for mesh in root.findall(".//mesh"):
            name, filename = mesh.get("name"), mesh.get("file")
            if name and filename:
                meshes.append((name, filename))
        for joint in root.findall(".//joint"):
            if joint.get("type", "hinge") == "hinge" and joint.get("name"):
                hinge_joints.append(str(joint.get("name")))
        for actuator_parent in root.findall(".//actuator"):
            for actuator in list(actuator_parent):
                name, joint = actuator.get("name"), actuator.get("joint")
                if name and joint:
                    actuators.append((name, joint))
        for sensor_parent in root.findall(".//sensor"):
            for sensor in list(sensor_parent):
                if sensor.get("name"):
                    sensors.add(str(sensor.get("name")))
        for key in root.findall(".//key"):
            qpos = key.get("qpos")
            if qpos:
                key_qpos_widths.append(len(qpos.split()))

    if len(compiler_meshdirs) != 1:
        report.error(
            "mjcf-meshdir",
            "expected one compiler meshdir, found {}".format(compiler_meshdirs),
        )
    else:
        # MuJoCo resolves meshdir against the top-level model directory after
        # includes are expanded. The X1 source contract therefore maps
        # mjcf/../meshes to the sibling meshes directory.
        mesh_root = (top.parent / compiler_meshdirs[0]).resolve()
        if boundary is not None and not inside(mesh_root, boundary):
            report.error("mjcf-meshdir", "compiler meshdir escapes the asset root")
        elif not mesh_root.is_dir():
            report.error("mjcf-meshdir", "compiler meshdir is missing: {}".format(mesh_root))
        else:
            missing = []
            for _, filename in meshes:
                mesh_path = (mesh_root / filename).resolve()
                if not inside(mesh_path, mesh_root) or not mesh_path.is_file():
                    missing.append(filename)
            if missing:
                report.error(
                    "mjcf-mesh-files",
                    "{} mesh references do not resolve: {}".format(
                        len(missing), ", ".join(sorted(set(missing))[:8])
                    ),
                )
            else:
                report.ok(
                    "mjcf-mesh-files",
                    "all {} MJCF mesh references resolve under compiler meshdir".format(len(meshes)),
                )

    if hinge_joints != EXPECTED_MJCF_JOINTS:
        report.error(
            "mjcf-joint-order",
            "actuated hinge order is {}, expected {}".format(
                hinge_joints, EXPECTED_MJCF_JOINTS
            ),
        )
    else:
        report.ok("mjcf-joint-order", "12 hinge joints match the policy action order")

    actuator_joints = [joint for _, joint in actuators]
    if actuator_joints != EXPECTED_MJCF_JOINTS:
        report.error(
            "mjcf-actuators",
            "actuator joint order is {}, expected {}".format(
                actuator_joints, EXPECTED_MJCF_JOINTS
            ),
        )
    else:
        report.ok("mjcf-actuators", "12 motors match the policy action order")

    missing_sensors = sorted(EXPECTED_SENSORS - sensors)
    if missing_sensors:
        report.error("mjcf-sensors", "missing required sensors: {}".format(missing_sensors))
    else:
        report.ok("mjcf-sensors", "orientation, angular-velocity, position, velocity, and acceleration sensors exist")

    if key_qpos_widths != [19]:
        report.error(
            "mjcf-keyframe",
            "expected one 19-value home keyframe (free base + 12 joints), got {}".format(
                key_qpos_widths
            ),
        )
    else:
        report.ok("mjcf-keyframe", "home keyframe has 19 qpos values")

    report.details["mjcf"] = {
        "documents": len(documents),
        "mesh_references": len(meshes),
        "hinge_joints": len(hinge_joints),
        "actuators": len(actuators),
        "sensors": len(sensors),
    }


def validate_urdf(path: Path, boundary: Optional[Path], report: Report) -> None:
    urdf = checked_file(path, boundary, report, "urdf-file")
    if urdf is None:
        return
    root = parse_xml(urdf, report, "urdf-parse")
    if root is None:
        return
    if root.tag != "robot" or root.get("name") != "x1":
        report.error("urdf-root", "URDF must be <robot name='x1'>")
        return
    revolute = [
        str(joint.get("name"))
        for joint in root.findall("joint")
        if joint.get("type") in ("revolute", "continuous") and joint.get("name")
    ]
    if revolute != EXPECTED_URDF_JOINTS:
        report.error(
            "urdf-joint-order",
            "URDF revolute order is {}, expected {}".format(
                revolute, EXPECTED_URDF_JOINTS
            ),
        )
    else:
        report.ok("urdf-joint-order", "12 URDF revolute joints align with MJCF after removing _joint suffix")

    missing: List[str] = []
    mesh_refs = []
    for mesh in root.findall(".//mesh"):
        filename = mesh.get("filename")
        if not filename:
            continue
        mesh_refs.append(filename)
        resolved = (urdf.parent / filename).resolve()
        if boundary is not None and not inside(resolved, boundary):
            missing.append(filename + " (escapes asset root)")
        elif not resolved.is_file():
            missing.append(filename)
    if missing:
        report.error(
            "urdf-mesh-files",
            "{} URDF mesh references do not resolve: {}".format(
                len(missing), ", ".join(sorted(set(missing))[:8])
            ),
        )
    else:
        report.ok(
            "urdf-mesh-files",
            "all {} URDF mesh references resolve relative to the URDF".format(len(mesh_refs)),
        )
    report.details["urdf"] = {
        "links": len(root.findall("link")),
        "joints": len(root.findall("joint")),
        "revolute_joints": len(revolute),
        "mesh_references": len(mesh_refs),
    }


def resolve_model_dir(args: argparse.Namespace, report: Report) -> Optional[Path]:
    base = args.logs_root.expanduser() / args.task / "exported_policies"
    selected: Optional[Path] = None
    if args.load_model is not None:
        candidate = args.load_model.expanduser()
        selected = candidate if candidate.is_absolute() else base / candidate
    elif args.discover_latest_model:
        if not base.is_dir():
            report.error("model-root", "exported policy root is missing: {}".format(base))
            return None
        try:
            directories = sorted(path for path in base.iterdir() if path.is_dir())
        except OSError as exc:
            report.error("model-root", "could not list {}: {}".format(base, exc))
            return None
        if not directories:
            report.error("model-root", "no timestamp directories exist under {}".format(base))
            return None
        selected = directories[-1]
        report.warn(
            "implicit-model-directory",
            "latest directory was selected lexicographically; pin --load-model for reproducibility",
        )
    return selected.resolve() if selected is not None else None


def validate_torchscript_archive(path: Path, report: Report) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        report.error("jit-file", "JIT artifact is missing or empty: {}".format(path))
        return
    if path.suffix != ".jit":
        report.warn("jit-name", "export normally writes policy_dh.jit; selected {}".format(path.name))
    if not zipfile.is_zipfile(str(path)):
        report.error("jit-archive", "artifact is not a TorchScript ZIP archive")
        return
    try:
        with zipfile.ZipFile(str(path), "r") as archive:
            names = archive.namelist()
    except (OSError, zipfile.BadZipFile) as exc:
        report.error("jit-archive", "could not inspect TorchScript archive: {}".format(exc))
        return
    markers = {
        "data.pkl": any(name.endswith("/data.pkl") or name == "data.pkl" for name in names),
        "constants.pkl": any(name.endswith("/constants.pkl") or name == "constants.pkl" for name in names),
        "version": any(name.endswith("/version") or name == "version" for name in names),
        "code": any("/code/" in name or name.startswith("code/") for name in names),
    }
    missing = sorted(name for name, present in markers.items() if not present)
    if missing:
        report.error("jit-archive", "TorchScript archive markers are missing: {}".format(missing))
        return
    report.ok(
        "jit-archive",
        "TorchScript archive structure is present; policy code was not loaded or executed",
    )


def validate_model_directory(path: Path, report: Report) -> None:
    if path.is_file():
        report.error(
            "load-model-contract",
            "native --load_model expects a directory, not the JIT file itself: {}".format(path),
        )
        return
    if not path.is_dir():
        report.error("load-model-contract", "model directory is missing: {}".format(path))
        return
    try:
        entries = sorted(path.iterdir(), key=lambda item: item.name)
    except OSError as exc:
        report.error("load-model-contract", "could not list model directory: {}".format(exc))
        return
    if len(entries) != 1 or not entries[0].is_file():
        report.error(
            "load-model-ambiguity",
            "model directory must contain exactly one file because the native final os.listdir selection is unsorted; found {}".format(
                [entry.name for entry in entries]
            ),
        )
        return
    artifact = entries[0]
    report.ok("load-model-contract", "--load_model resolves to one pinned artifact directory")
    validate_torchscript_archive(artifact, report)
    report.details["selected_jit"] = artifact.name


def distribution_version(name: str) -> Optional[str]:
    try:
        from importlib import metadata

        return metadata.version(name)
    except Exception:
        return None


def module_present(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def runtime_metadata(report: Report, require_runtime: bool) -> None:
    runtime = {
        "python": "{}.{}.{}".format(*sys.version_info[:3]),
        "mujoco": distribution_version("mujoco"),
        "mujoco-python-viewer": distribution_version("mujoco-python-viewer"),
        "pygame": distribution_version("pygame"),
        "torch": distribution_version("torch"),
        "scipy": distribution_version("scipy"),
        "isaacgym_module": module_present("isaacgym"),
        "display": bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")),
        "joysticks": sorted(str(path) for path in Path("/dev/input").glob("js*")) if Path("/dev/input").is_dir() else [],
    }
    report.details["runtime_metadata"] = runtime

    def missing_or_error(condition: bool, code: str, message: str) -> None:
        if condition:
            report.ok(code, message)
        elif require_runtime:
            report.error(code, message)
        else:
            report.warn(code, message)

    missing_or_error(
        sys.version_info[:2] == (3, 8),
        "python-version",
        "native compatibility stack expects Python 3.8; detected {}".format(runtime["python"]),
    )
    missing_or_error(
        runtime["mujoco"] == EXPECTED_MUJOCO,
        "mujoco-version",
        "native dependency pin is mujoco=={}; detected {}".format(
            EXPECTED_MUJOCO, runtime["mujoco"] or "not installed"
        ),
    )
    for module, distribution in (
        ("mujoco_viewer", "mujoco-python-viewer"),
        ("pygame", "pygame"),
        ("torch", "torch"),
        ("scipy", "scipy"),
    ):
        missing_or_error(
            module_present(module),
            "module-" + module.replace("_", "-"),
            "required native module {} ({}) is {}".format(
                module,
                distribution,
                "discoverable" if module_present(module) else "not discoverable",
            ),
        )

    if runtime["isaacgym_module"]:
        report.ok(
            "isaacgym-module",
            "isaacgym is discoverable; still verify the vendor Preview 4 example and CUDA/PhysX stack",
        )
    else:
        report.blocked(
            "isaacgym-module",
            "full native sim2sim imports humanoid.envs and cannot run until NVIDIA Isaac Gym Preview 4 is available",
        )
    missing_or_error(
        runtime["display"],
        "display",
        "interactive native runtime requires DISPLAY or WAYLAND_DISPLAY; no viewer is opened by this helper",
    )
    missing_or_error(
        bool(runtime["joysticks"]),
        "joystick",
        "interactive joystick control expects a visible /dev/input/js* device; no device is opened by this helper",
    )


def compile_mujoco(path: Path, report: Report, require_runtime: bool) -> None:
    code = r"""
import json, sys
import mujoco
model = mujoco.MjModel.from_xml_path(sys.argv[1])
print(json.dumps({
  'version': mujoco.__version__, 'nq': model.nq, 'nv': model.nv,
  'nu': model.nu, 'nbody': model.nbody, 'nsensor': model.nsensor,
  'timestep': model.opt.timestep
}))
"""
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code, str(path)],
            text=True,
            capture_output=True,
            timeout=45,
            check=False,
        )
    except Exception as exc:
        report.error("mujoco-compile", "child-process compile failed: {}".format(exc))
        return
    if proc.returncode != 0:
        report.error(
            "mujoco-compile",
            "MJCF compile failed without a viewer: {}".format(
                (proc.stderr or proc.stdout).strip() or "exit {}".format(proc.returncode)
            ),
        )
        return
    try:
        result = json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as exc:
        report.error("mujoco-compile", "invalid compile probe output: {}".format(exc))
        return
    report.details["mujoco_compile"] = result
    expected = {
        "nq": 19,
        "nv": 18,
        "nu": 12,
        "nbody": 31,
        "nsensor": 29,
        "timestep": 0.001,
    }
    mismatches = {
        key: {"actual": result.get(key), "expected": value}
        for key, value in expected.items()
        if result.get(key) != value
    }
    if mismatches:
        report.error("mujoco-compile-shape", "compiled model differs: {}".format(mismatches))
    else:
        report.ok("mujoco-compile-shape", "MJCF compiles without a viewer with nq=19, nv=18, nu=12")
    if result.get("version") != EXPECTED_MUJOCO:
        message = "compile used mujoco {}, but the native pin is {}".format(
            result.get("version"), EXPECTED_MUJOCO
        )
        if require_runtime:
            report.error("mujoco-compile-version", message)
        else:
            report.warn("mujoco-compile-version", message)


def print_report(report: Report, as_json: bool) -> None:
    payload = {
        "status": "failed" if report.has_errors() else "isolated-validation-ok",
        "full_native_status": (
            "blocked-required-backend" if report.has_blocks() else "backend-metadata-present"
        ),
        "checks": report.checks,
        "details": report.details,
        "safety": {
            "viewer_opened": False,
            "joystick_opened": False,
            "policy_deserialized": False,
            "simulation_stepped": False,
        },
    }
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    print("X1 sim2sim preflight")
    for item in report.checks:
        print("{level}: {code}: {message}".format(**item))
    print("status={}".format(payload["status"]))
    print("full_native_status={}".format(payload["full_native_status"]))
    print("safety=viewer:false joystick:false policy-load:false simulation-step:false")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    report = Report()
    if args.task != TASK:
        report.error(
            "task-contract",
            "only {} is registered for this X1 sim2sim contract; got {}".format(
                TASK, args.task
            ),
        )
    else:
        report.ok("task-contract", "task is the registered x1_dh_stand configuration")

    boundary = args.asset_root.expanduser().resolve() if args.asset_root else None
    if boundary is not None and not boundary.is_dir():
        report.error("asset-root", "asset root is not a directory: {}".format(args.asset_root))
    mjcf = args.mjcf_model
    urdf = args.urdf
    if boundary is not None:
        mjcf = mjcf or boundary / "mjcf" / "xyber_x1_flat.xml"
        urdf = urdf or boundary / "urdf" / "x1.urdf"
    if mjcf is not None:
        validate_mjcf(mjcf, boundary, report)
    if urdf is not None:
        validate_urdf(urdf, boundary, report)
    if args.compile_mujoco:
        if mjcf is None:
            report.error("mujoco-compile", "--compile-mujoco requires --asset-root or --mjcf-model")
        else:
            compile_path = mjcf.expanduser().resolve()
            if compile_path.is_file():
                compile_mujoco(compile_path, report, args.require_runtime)

    model_dir = resolve_model_dir(args, report)
    if model_dir is not None:
        validate_model_directory(model_dir, report)

    runtime_metadata(report, args.require_runtime)
    if args.require_runtime and report.has_blocks():
        report.error(
            "required-backend-gate",
            "--require-runtime cannot pass while Isaac Gym Preview 4 is blocked",
        )
    print_report(report, args.json)
    return 1 if report.has_errors() else 0


if __name__ == "__main__":
    raise SystemExit(main())
