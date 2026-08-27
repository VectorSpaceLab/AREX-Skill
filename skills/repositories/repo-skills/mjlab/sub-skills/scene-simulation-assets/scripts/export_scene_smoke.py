#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import mujoco

import mjlab.tasks  # noqa: F401  # register packaged tasks
from mjlab.entity import EntityCfg
from mjlab.scene import Scene, SceneCfg
from mjlab.scripts.export_scene import ENTITY_ALIASES
from mjlab.tasks.registry import list_tasks, load_env_cfg
from mjlab.utils.lab_api.string import string_to_callable


def build_arg_parser() -> argparse.ArgumentParser:
  parser = argparse.ArgumentParser(
    description="Resolve an mjlab task/entity target, export its scene, and verify scene.xml exists."
  )
  parser.add_argument(
    "--target",
    required=True,
    help="Task ID, asset-zoo alias (g1, go1, yam), or module:callable returning EntityCfg/SceneCfg.",
  )
  parser.add_argument("--zip", action="store_true", help="Write <output-dir>.zip.")
  parser.add_argument("--strict-compile", action="store_true", help="Fail if exported scene.xml cannot be compiled back by MuJoCo.")
  parser.add_argument("--keep-output", action="store_true", help="Keep auto-created temporary output.")
  parser.add_argument("--output-dir", type=Path, help="Directory base for export.")
  return parser


def _format_known_targets(task_ids: list[str]) -> str:
  aliases = ", ".join(sorted(ENTITY_ALIASES))
  tasks = "\n".join(f"  - {task_id}" for task_id in task_ids)
  return f"Available aliases: {aliases}\nAvailable task IDs:\n{tasks}"


def _scene_from_import_path(target: str) -> tuple[Scene, str]:
  factory = string_to_callable(target)
  cfg = factory()
  if isinstance(cfg, SceneCfg):
    return Scene(cfg, device="cpu"), f"scene import path {target}"
  if isinstance(cfg, EntityCfg):
    return Scene(SceneCfg(entities={"robot": cfg}), device="cpu"), f"entity import path {target}"
  raise TypeError(f"import path callable must return EntityCfg or SceneCfg, got {type(cfg).__name__}")


def resolve_scene(target: str) -> tuple[Scene, str]:
  task_ids = list_tasks()
  resolved = ENTITY_ALIASES.get(target, target)
  if resolved in task_ids:
    env_cfg = load_env_cfg(resolved)
    return Scene(env_cfg.scene, device="cpu"), f"task {resolved}"
  if ":" in resolved:
    return _scene_from_import_path(resolved)
  raise ValueError(f"Unknown target {target!r}.\n{_format_known_targets(task_ids)}")


def _clean_existing_export(base: Path, zip_export: bool) -> None:
  if base.exists():
    if base.is_dir():
      shutil.rmtree(base)
    else:
      base.unlink()
  zip_path = base.with_suffix(".zip")
  if zip_export and zip_path.exists():
    zip_path.unlink()


def _extract_scene_xml(base: Path, zip_export: bool) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
  if not zip_export:
    xml = base / "scene.xml"
    if not xml.is_file():
      raise FileNotFoundError(f"expected exported scene.xml at {xml}")
    return xml, None

  zip_path = base.with_suffix(".zip")
  if not zip_path.is_file():
    raise FileNotFoundError(f"expected exported zip archive at {zip_path}")
  tmp = tempfile.TemporaryDirectory(prefix="mjlab-export-verify-")
  with zipfile.ZipFile(zip_path) as zf:
    if "scene.xml" not in set(zf.namelist()):
      raise RuntimeError("exported zip archive does not contain scene.xml")
    zf.extractall(tmp.name)
  return Path(tmp.name) / "scene.xml", tmp


def _try_compile(xml: Path) -> tuple[bool, str]:
  try:
    model = mujoco.MjModel.from_xml_path(str(xml))
  except Exception as exc:  # smoke helper should report this clearly
    return False, f"{type(exc).__name__}: {exc}"
  return True, f"nbody={model.nbody}, ngeom={model.ngeom}"


def main(argv: list[str] | None = None) -> int:
  args = build_arg_parser().parse_args(argv)
  temp_root: Path | None = None
  extracted_tmp: tempfile.TemporaryDirectory[str] | None = None
  try:
    scene, target_kind = resolve_scene(args.target)
    if args.output_dir is None:
      temp_root = Path(tempfile.mkdtemp(prefix="mjlab-scene-export-"))
      output_base = temp_root / "scene"
    else:
      output_base = args.output_dir.expanduser()

    _clean_existing_export(output_base, args.zip)
    scene.write(output_base, zip=args.zip)
    xml, extracted_tmp = _extract_scene_xml(output_base, args.zip)
    ok, compile_info = _try_compile(xml)
    if args.strict_compile and not ok:
      raise RuntimeError(f"exported scene.xml compile failed: {compile_info}")

    artifact = output_base.with_suffix(".zip") if args.zip else output_base
    print(f"Target: {target_kind}")
    print(f"Verified scene.xml: {xml}")
    print(f"Export artifact: {artifact}")
    if ok:
      print(f"Compiled exported XML: {compile_info}")
    else:
      print(f"Compile warning (non-strict): {compile_info}")
    if temp_root is not None and args.keep_output:
      print(f"Kept temporary export tree: {temp_root}")
    return 0
  except Exception as exc:
    print(f"export_scene_smoke failed: {type(exc).__name__}: {exc}", file=sys.stderr)
    return 1
  finally:
    if extracted_tmp is not None:
      extracted_tmp.cleanup()
    if temp_root is not None and not args.keep_output:
      shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
  raise SystemExit(main())
