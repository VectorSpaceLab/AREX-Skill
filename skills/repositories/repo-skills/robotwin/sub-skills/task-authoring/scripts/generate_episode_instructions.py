#!/usr/bin/env python3
"""Deterministically expand RoboTwin episode instructions without hosted APIs.

This helper mirrors the repository's placeholder-expansion contract while
avoiding Azure/OpenAI/DeepSeek/Moonshot calls. It reads task instruction JSON,
scene_info episode metadata, and optional object-description JSON files, then
prints or writes per-episode instruction files.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - exercised in minimal environments
    yaml = None


ARM_KEY_RE = re.compile(r"^[a-z]$")
PLACEHOLDER_RE = re.compile(r"{([^}]+)}")


def extract_placeholders(instruction: str) -> List[str]:
    """Return placeholder names without braces, preserving order."""
    return PLACEHOLDER_RE.findall(instruction)


def strip_episode_params(episode_params: Mapping[str, Any]) -> Dict[str, str]:
    """Normalize keys like '{A}' and values from scene_info into strings."""
    return {str(key).strip("{}"): str(value) for key, value in episode_params.items()}


def is_arm_key(key: str) -> bool:
    return bool(ARM_KEY_RE.fullmatch(key))


def deterministic_order(items: Sequence[str], rng: random.Random) -> List[str]:
    ordered = list(items)
    rng.shuffle(ordered)
    return ordered


def filter_instructions(
    instructions: Sequence[str],
    episode_params: Mapping[str, Any],
    rng: random.Random,
) -> List[str]:
    """Keep templates whose placeholders match episode params.

    A template may either use exactly the available placeholders or omit all arm
    placeholders while retaining every non-arm placeholder. This preserves the
    repository's arm-optional language behavior.
    """
    stripped = strip_episode_params(episode_params)
    episode_keys = set(stripped)
    arm_params = {key for key in episode_keys if is_arm_key(key)}
    filtered: List[str] = []

    for instruction in deterministic_order(instructions, rng):
        placeholders = set(extract_placeholders(instruction))
        exact = placeholders == episode_keys
        arm_free_variant = (
            bool(arm_params)
            and placeholders.union(arm_params) == episode_keys
            and not placeholders.intersection(arm_params)
        )
        if exact or arm_free_variant:
            filtered.append(instruction)
    return filtered


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        raise SystemExit(f"Missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}")


def load_yaml_file(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise SystemExit("PyYAML is required to read task configs. Install PyYAML or pass --scene-info directly.")
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    except FileNotFoundError:
        raise SystemExit(f"Missing task config: {path}")
    except Exception as exc:
        raise SystemExit(f"Could not parse YAML {path}: {exc}")
    if not isinstance(data, dict):
        raise SystemExit(f"Task config must be a mapping: {path}")
    return data


def resolve_under_repo(repo_root: Path, raw_path: str | Path) -> Path:
    path = Path(raw_path).expanduser()
    return path if path.is_absolute() else repo_root / path


def embodiment_dir_from_config(config: Mapping[str, Any]) -> Optional[str]:
    embodiment = config.get("embodiment")
    if isinstance(embodiment, str):
        name = embodiment
    elif isinstance(embodiment, list) and len(embodiment) == 1:
        name = str(embodiment[0])
    elif isinstance(embodiment, list) and len(embodiment) >= 2:
        name = f"{embodiment[0]}+{embodiment[1]}"
    else:
        return None
    return re.sub(r"[^A-Za-z0-9_]+", "_", name).lower()


def discover_scene_info(repo_root: Path, task_name: str, setting: str) -> Path:
    config_path = repo_root / "env_cfg" / "task_config" / f"{setting}.yml"
    config = load_yaml_file(config_path)
    save_path = resolve_under_repo(repo_root, config.get("save_path", "./data"))
    emb_dir = embodiment_dir_from_config(config)

    candidates: List[Path] = []
    if emb_dir:
        candidates.append(save_path / setting / task_name / emb_dir / "scene_info.json")
    candidates.append(save_path / task_name / setting / "scene_info.json")
    if emb_dir:
        candidates.append(save_path / task_name / setting / emb_dir / "scene_info.json")
    candidates.append(save_path / "scene_info.json")

    for candidate in candidates:
        if candidate.exists():
            return candidate

    joined = "\n  - ".join(str(path) for path in candidates)
    raise SystemExit(
        "Could not discover scene_info.json. Pass --scene-info explicitly. Tried:\n  - " + joined
    )


def load_task_data(task_json: Path) -> Dict[str, Any]:
    data = load_json(task_json)
    if not isinstance(data, dict):
        raise SystemExit(f"Task instruction JSON must be an object: {task_json}")
    data.setdefault("seen", [])
    data.setdefault("unseen", [])
    for split in ("seen", "unseen"):
        if not isinstance(data.get(split), list):
            raise SystemExit(f"'{split}' must be a list in {task_json}")
        data[split] = [str(item) for item in data[split]]
    return data


def extract_episodes(scene_info: Any) -> List[Dict[str, Any]]:
    """Extract the per-episode info mapping from scene_info JSON."""
    if isinstance(scene_info, list):
        raw_episodes: Iterable[Any] = scene_info
    elif isinstance(scene_info, dict):
        # A single episode may be stored as {'info': {...}}; otherwise use each
        # top-level episode entry in insertion order.
        if set(scene_info.keys()) == {"info"} or (
            "info" in scene_info and isinstance(scene_info.get("info"), dict) and not any(
                str(key).startswith("episode") for key in scene_info.keys()
            )
        ):
            raw_episodes = [scene_info]
        else:
            raw_episodes = scene_info.values()
    else:
        raise SystemExit("scene_info JSON must be a list or object")

    episodes: List[Dict[str, Any]] = []
    for item in raw_episodes:
        if isinstance(item, dict) and isinstance(item.get("info"), dict):
            episodes.append(dict(item["info"]))
        elif isinstance(item, dict):
            episodes.append(dict(item))
        else:
            episodes.append({})
    return episodes


def object_description_path(object_root: Path, value: str) -> Path:
    return object_root / f"{value}.json"


def choose_object_phrase(
    object_root: Path,
    value: str,
    split: str,
    rng: random.Random,
) -> Optional[str]:
    path = object_description_path(object_root, value)
    if not path.exists():
        return None
    data = load_json(path)
    if not isinstance(data, dict):
        raise SystemExit(f"Object-description JSON must be an object: {path}")

    choices = data.get(split) if isinstance(data.get(split), list) else []
    if split == "unseen" and not choices:
        choices = data.get("seen") if isinstance(data.get("seen"), list) else []
    if not choices and isinstance(data.get("raw_description"), str):
        choices = [data["raw_description"]]
    if not choices:
        raise SystemExit(f"No usable descriptions in {path}")
    return str(rng.choice(choices))


def replace_placeholders(
    instruction: str,
    episode_params: Mapping[str, Any],
    split: str,
    object_root: Path,
    rng: random.Random,
) -> str:
    stripped = strip_episode_params(episode_params)
    rendered = instruction
    for key in sorted(stripped.keys()):
        value = stripped[key]
        replacement: str
        phrase = choose_object_phrase(object_root, value, split, rng)
        if phrase is not None:
            replacement = f"the {phrase}"
        elif "/" in value or "\\" in value:
            raise SystemExit(
                f"'{value}' looks like an object-description id, but {object_description_path(object_root, value)} does not exist"
            )
        elif is_arm_key(key):
            replacement = f"the {value} arm"
        else:
            replacement = value
        rendered = rendered.replace("{" + key + "}", replacement)
    return rendered


def expand_split(
    templates: Sequence[str],
    episode_params: Mapping[str, Any],
    split: str,
    object_root: Path,
    max_num: int,
    rng: random.Random,
    dedupe: bool,
) -> List[str]:
    if max_num <= 0:
        return []
    filtered = filter_instructions(templates, episode_params, rng)
    results: List[str] = []
    seen_strings: set[str] = set()
    stale_cycles = 0

    while filtered and len(results) < max_num:
        before = len(results)
        for template in filtered:
            if len(results) >= max_num:
                break
            rendered = replace_placeholders(template, episode_params, split, object_root, rng)
            if dedupe and rendered in seen_strings:
                continue
            results.append(rendered)
            seen_strings.add(rendered)
        if len(results) == before:
            stale_cycles += 1
            if stale_cycles >= 5:
                break
        else:
            stale_cycles = 0
    return results


def generate_episode_descriptions(
    task_data: Mapping[str, Any],
    episodes: Sequence[Mapping[str, Any]],
    object_root: Path,
    max_num: int,
    seed: int,
    dedupe: bool,
) -> List[Dict[str, Any]]:
    generated: List[Dict[str, Any]] = []
    for index, episode in enumerate(episodes):
        episode_rng = random.Random(seed + index * 1009)
        seen = expand_split(task_data.get("seen", []), episode, "seen", object_root, max_num, episode_rng, dedupe)
        unseen = expand_split(task_data.get("unseen", []), episode, "unseen", object_root, max_num, episode_rng, dedupe)
        generated.append({"episode_index": index, "seen": seen, "unseen": unseen})
    return generated


def output_name(index: int, filename_style: str) -> str:
    if filename_style == "legacy":
        return f"episode{index}.json"
    return f"episode_{index:07d}.json"


def save_outputs(outputs: Sequence[Mapping[str, Any]], output_dir: Path, filename_style: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for item in outputs:
        index = int(item["episode_index"])
        path = output_dir / output_name(index, filename_style)
        payload = {"seen": list(item.get("seen", [])), "unseen": list(item.get("unseen", []))}
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")


def print_preview(outputs: Sequence[Mapping[str, Any]], limit: int = 3) -> None:
    preview = []
    for item in outputs[:limit]:
        preview.append(
            {
                "episode_index": item.get("episode_index"),
                "seen_count": len(item.get("seen", [])),
                "unseen_count": len(item.get("unseen", [])),
                "seen_preview": list(item.get("seen", []))[:2],
                "unseen_preview": list(item.get("unseen", []))[:2],
            }
        )
    print(json.dumps(preview, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Expand RoboTwin episode instructions without hosted model calls.")
    parser.add_argument("--repo-root", default=".", help="RoboTwin workspace root; default: current directory")
    parser.add_argument("--task", dest="task_name", help="Task name, for example beat_block_hammer")
    parser.add_argument("--setting", help="Task config name used to discover scene_info.json")
    parser.add_argument("--task-json", help="Task instruction JSON; default: description/task_instruction/<task>.json")
    parser.add_argument("--scene-info", help="scene_info.json path; avoids discovery from --setting")
    parser.add_argument("--object-description-root", help="Object-description root; default: description/objects_description")
    parser.add_argument("--output-dir", help="Where to write episode instruction JSON; default: scene_info directory/instruction")
    parser.add_argument("--filename-style", choices=["xpolicylab", "legacy"], default="xpolicylab")
    parser.add_argument("--max-num", type=int, default=100, help="Maximum instructions per split per episode")
    parser.add_argument("--seed", type=int, default=0, help="Deterministic seed for template/phrase selection")
    parser.add_argument("--dedupe", action="store_true", help="Drop duplicate expanded strings")
    parser.add_argument("--dry-run", action="store_true", help="Print preview and do not write files")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve()

    task_json = resolve_under_repo(repo_root, args.task_json) if args.task_json else None
    task_name = args.task_name or (task_json.stem if task_json is not None else None)
    if not task_name:
        raise SystemExit("Pass --task or --task-json")

    if task_json is None:
        task_json = repo_root / "description" / "task_instruction" / f"{task_name}.json"
    object_root = (
        resolve_under_repo(repo_root, args.object_description_root)
        if args.object_description_root
        else repo_root / "description" / "objects_description"
    )
    if args.scene_info:
        scene_info_path = resolve_under_repo(repo_root, args.scene_info)
    else:
        if not args.setting:
            raise SystemExit("Pass --setting or --scene-info")
        scene_info_path = discover_scene_info(repo_root, task_name, args.setting)

    task_data = load_task_data(task_json)
    episodes = extract_episodes(load_json(scene_info_path))
    outputs = generate_episode_descriptions(
        task_data=task_data,
        episodes=episodes,
        object_root=object_root,
        max_num=args.max_num,
        seed=args.seed,
        dedupe=args.dedupe,
    )

    print(
        f"Expanded {len(outputs)} episode(s) for task '{task_name}' "
        f"from {scene_info_path.name} using max_num={args.max_num}, seed={args.seed}."
    )
    print_preview(outputs)

    if args.dry_run:
        print("Dry run: no files written.")
        return 0

    output_dir = resolve_under_repo(repo_root, args.output_dir) if args.output_dir else scene_info_path.parent / "instruction"
    save_outputs(outputs, output_dir, args.filename_style)
    print(f"Wrote instructions to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
