#!/usr/bin/env python3
"""Self-contained UnrealCV plugin build, install, and packaging helper.

This helper uses the packaged UnrealCV source snapshot under
``references/unrealcv-source/`` by default. It does not need the original
UnrealCV checkout and does not import the ``unrealcv`` Python package.

Safe defaults:
- Dry-run mode is used unless ``--execute`` is passed.
- Relative descriptor paths are resolved inside the packaged source snapshot
  before the caller's working directory.
- Build outputs default to the caller's working directory, not the skill bundle.
"""

from __future__ import annotations

import argparse
import glob
import json
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Optional

PLUGIN_ITEMS = ["UnrealCV.uplugin", "Config", "Content", "Resources", "Source"]


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_source_root() -> Path:
    return _skill_root() / "references" / "unrealcv-source"


def get_platform_name() -> Optional[str]:
    """Return the Unreal Automation Tool platform name for this host."""
    return {
        "Darwin": "Mac",
        "Windows": "Win64",
        "Linux": "Linux",
    }.get(platform.system())


def get_plugin_version(plugin_descriptor: Path) -> str:
    """Read VersionName from an Unreal plugin descriptor."""
    data = json.loads(plugin_descriptor.read_text(encoding="utf-8"))
    return str(data.get("VersionName", "unknown"))


def _resolve_descriptor(descriptor_file: Optional[str], source_root: Path) -> Path:
    if descriptor_file is None:
        for candidate in (source_root / "UnrealCV.uplugin", source_root / "UnrealCV.uproject"):
            if candidate.is_file():
                return candidate.resolve()
        raise SystemExit(f"No packaged UnrealCV descriptor found under {source_root}")

    candidate = Path(descriptor_file).expanduser()
    search_paths: list[Path]
    if candidate.is_absolute():
        search_paths = [candidate]
    else:
        # Prefer the packaged bundle for self-contained operation. A caller who
        # wants another checkout should pass --source-root or an absolute path.
        search_paths = [source_root / candidate, candidate]

    for path in search_paths:
        if path.is_file():
            return path.resolve()

    raise SystemExit(f"descriptor file not found: {descriptor_file}")


def _default_output(descriptor: Path) -> Path:
    if descriptor.suffix == ".uplugin":
        return Path.cwd() / "Plugins" / "UnrealCV"
    if descriptor.suffix == ".uproject":
        return Path.cwd() / "UE4Binaries" / descriptor.stem
    raise SystemExit("descriptor_file must end with .uplugin or .uproject")


def _find_engine_candidates(platform_name: str) -> list[Path]:
    if platform_name == "Win64":
        patterns = [
            r"C:\Program Files\Epic Games\UE_4.??",
            r"C:\Program Files\Epic Games\UE_5.??",
            r"D:\Program Files\Epic Games\UE_4.??",
            r"D:\Program Files\Epic Games\UE_5.??",
        ]
    elif platform_name == "Mac":
        patterns = ["/Users/Shared/Epic Games/UE_4.??", "/Users/Shared/Epic Games/UE_5.??"]
    else:
        patterns = [
            "~/UnrealEngine",
            "~/workspace/UnrealEngine",
            "~/workspace/UE4??",
            "~/workspace/UE_4.??",
            "~/workspace/UE_5.??",
        ]
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(Path(path).expanduser() for path in glob.glob(str(Path(pattern).expanduser())))
    return matches


def _resolve_engine_root(ue4: Optional[str], require: bool) -> Optional[Path]:
    platform_name = get_platform_name()
    if not platform_name:
        if require:
            raise SystemExit(f"Unsupported host platform for Unreal Engine: {platform.system()}")
        return None

    if ue4:
        root = Path(ue4).expanduser().resolve()
        if require and not root.exists():
            raise SystemExit(f"Unreal Engine root not found: {root}")
        return root

    candidates = _find_engine_candidates(platform_name)
    if len(candidates) == 1:
        return candidates[0].resolve()
    if require:
        message = "Could not infer an Unreal Engine root; pass --ue4/--UE4 explicitly."
        if candidates:
            message += " Candidates: " + ", ".join(str(path) for path in candidates)
        raise SystemExit(message)
    return candidates[0].resolve() if candidates else None


def _uat_relative_path() -> Path:
    platform_name = get_platform_name()
    rel = {
        "Linux": Path("Engine/Build/BatchFiles/RunUAT.sh"),
        "Mac": Path("Engine/Build/BatchFiles/RunUAT.sh"),
        "Win64": Path("Engine/Build/BatchFiles/RunUAT.bat"),
    }.get(platform_name or "")
    if rel is None:
        raise SystemExit(f"Unsupported host platform for UAT: {platform.system()}")
    return rel


def _uat_path(engine_root: Path) -> Path:
    path = engine_root / _uat_relative_path()
    if not path.is_file():
        raise SystemExit(f"RunUAT script not found: {path}")
    return path


def _uat_path_for_display(engine_root: Optional[Path]) -> Path:
    return engine_root / _uat_relative_path() if engine_root else Path("<RunUAT>")


def _build_command(uat: Path, descriptor: Path, output: Path) -> list[str]:
    platform_name = get_platform_name() or "Unknown"
    if descriptor.suffix == ".uplugin":
        return [
            str(uat),
            "BuildPlugin",
            f"-plugin={descriptor}",
            f"-package={output}",
            "-rocket",
            f"-targetplatforms={platform_name}",
        ]
    return [
        str(uat),
        "BuildCookRun",
        f"-project={descriptor}",
        f"-archivedirectory={output}",
        f"-platform={platform_name}",
        "-clientconfig=Development",
        "-serverconfig=Development",
        "-noP4",
        "-allmaps",
        "-stage",
        "-pak",
        "-archive",
        "-cook",
        "-build",
    ]


def _copy_tree_contents(source: Path, target: Path, overwrite: bool) -> None:
    if target.exists():
        if not overwrite:
            raise SystemExit(f"Target exists; pass --overwrite to replace it: {target}")
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def _make_plugin_source_tree(source_root: Path, destination: Path, overwrite: bool) -> None:
    if destination.exists():
        if not overwrite:
            raise SystemExit(f"Plugin destination exists; pass --overwrite to replace it: {destination}")
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for item in PLUGIN_ITEMS:
        source = source_root / item
        if not source.exists():
            raise SystemExit(f"Required bundled plugin item missing: {source}")
        target = destination / item
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)


def _resolve_plugin_install_folder(target: str) -> Path:
    target_path = Path(target).expanduser().resolve()
    if target_path.name == "UnrealCV":
        return target_path
    if target_path.name == "Plugins":
        return target_path / "UnrealCV"
    if (target_path / "Engine").exists() or target_path.name.startswith("UE_"):
        return target_path / "Engine" / "Plugins" / "UnrealCV"
    if list(target_path.glob("*.uproject")):
        return target_path / "Plugins" / "UnrealCV"
    return target_path / "UnrealCV"


def _append_force_debug_view_modes(target: str, execute: bool) -> None:
    target_path = Path(target).expanduser().resolve()
    ini_path = target_path if target_path.suffix.lower() == ".ini" else target_path / "Engine" / "Config" / "ConsoleVariables.ini"
    line = "r.ForceDebugViewModes = 1"
    if not execute:
        print(f"Would ensure '{line}' is present in: {ini_path}")
        return
    ini_path.parent.mkdir(parents=True, exist_ok=True)
    existing = ini_path.read_text(encoding="utf-8", errors="ignore") if ini_path.exists() else ""
    if line not in existing:
        with ini_path.open("a", encoding="utf-8") as handle:
            if existing and not existing.endswith("\n"):
                handle.write("\n")
            handle.write(line + "\n")
    print(f"Ensured packaged-binary config in {ini_path}")


def _print_command(command: Iterable[str]) -> None:
    print(" ".join(str(part) for part in command))


def main() -> int:
    parser = argparse.ArgumentParser(description="Self-contained UnrealCV plugin build/package helper")
    parser.add_argument(
        "descriptor_file",
        nargs="?",
        default=None,
        help=".uplugin or .uproject to build/package; defaults to the packaged UnrealCV descriptor",
    )
    parser.add_argument(
        "--source-root",
        default=str(_default_source_root()),
        help="Packaged UnrealCV source snapshot or another source root",
    )
    parser.add_argument("--ue4", "--UE4", dest="ue4", help="Path to the Unreal Engine root")
    parser.add_argument("--output", help="Output folder for the built plugin or packaged binary")
    parser.add_argument("--install", action="store_true", help="Install the built plugin into the Unreal Engine after build")
    parser.add_argument("--install-target", help="Copy the built plugin output into this project, engine, Plugins, or UnrealCV folder")
    parser.add_argument("--copy-plugin-source-to", help="Copy the bundled UnrealCV plugin source tree into this project, engine, Plugins, or UnrealCV folder and exit")
    parser.add_argument("--configure-console-variables", help="Ensure r.ForceDebugViewModes = 1 in an Engine root or ConsoleVariables.ini")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output or install targets")
    parser.add_argument("--dry-run", action="store_true", help="Print inferred actions without running them")
    parser.add_argument("--execute", action="store_true", help="Actually run build, copy, or config actions")
    args = parser.parse_args()

    source_root = Path(args.source_root).expanduser().resolve()
    if not source_root.is_dir():
        raise SystemExit(f"Source root not found: {source_root}")

    should_execute = args.execute and not args.dry_run

    if args.configure_console_variables:
        _append_force_debug_view_modes(args.configure_console_variables, should_execute)
        if not args.copy_plugin_source_to and not args.install and not args.install_target and args.descriptor_file is None:
            return 0

    if args.copy_plugin_source_to:
        destination = _resolve_plugin_install_folder(args.copy_plugin_source_to)
        if should_execute:
            _make_plugin_source_tree(source_root, destination, args.overwrite)
            print(f"Copied bundled UnrealCV plugin source to {destination}")
        else:
            print(f"Would copy bundled UnrealCV plugin source from {source_root} to {destination}")
        return 0

    descriptor = _resolve_descriptor(args.descriptor_file, source_root)
    if args.install and descriptor.suffix != ".uplugin":
        raise SystemExit("--install only applies to .uplugin builds")

    output = Path(args.output).expanduser().resolve() if args.output else _default_output(descriptor).resolve()
    engine_root = _resolve_engine_root(args.ue4, require=should_execute)
    uat = _uat_path(engine_root) if should_execute and engine_root else _uat_path_for_display(engine_root)
    command = _build_command(uat, descriptor, output)

    print(f"Using packaged UnrealCV source snapshot: {source_root}")
    if descriptor.suffix == ".uplugin":
        print(f"Plugin version: {get_plugin_version(descriptor)}")
    print(f"Descriptor: {descriptor}")
    print(f"Output: {output}")
    print("UAT command:")
    _print_command(command)

    if not should_execute:
        if args.install:
            install_folder = engine_root / "Engine" / "Plugins" / "UnrealCV" if engine_root else "<UE root>/Engine/Plugins/UnrealCV"
            print(f"Would install built plugin into: {install_folder}")
        if args.install_target:
            print(f"Would copy built plugin output into: {_resolve_plugin_install_folder(args.install_target)}")
        return 0

    if output.exists() and args.overwrite:
        if output.is_dir():
            shutil.rmtree(output)
        else:
            output.unlink()
    elif output.exists() and not args.overwrite:
        raise SystemExit(f"Output folder exists; pass --overwrite to replace it: {output}")

    subprocess.check_call(command, cwd=str(source_root))

    if args.install:
        if engine_root is None:
            raise SystemExit("--install requires --ue4/--UE4 or a discoverable Unreal Engine root")
        install_folder = _resolve_plugin_install_folder(str(engine_root))
        _copy_tree_contents(output, install_folder, args.overwrite)
        print(f"Installed built plugin to {install_folder}")

    if args.install_target:
        install_folder = _resolve_plugin_install_folder(args.install_target)
        _copy_tree_contents(output, install_folder, args.overwrite)
        print(f"Copied built plugin output to {install_folder}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
