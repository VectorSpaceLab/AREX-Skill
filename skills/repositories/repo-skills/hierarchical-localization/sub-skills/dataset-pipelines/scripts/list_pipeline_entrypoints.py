#!/usr/bin/env python3
"""List known hloc dataset pipeline entrypoints safely.

This helper is static: it does not import hloc or run any dataset workflow.
Use it to plan which route to take and to surface safe `--help` commands.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Iterable


@dataclass(frozen=True)
class Entry:
    id: str
    title: str
    kind: str
    entrypoint: str
    default_dataset: str
    default_outputs: str
    prerequisites: str
    notes: str
    aliases: tuple[str, ...]
    help_command: str | None = None


ENTRIES: tuple[Entry, ...] = (
    Entry(
        id="aachen-v1.0",
        title="Aachen Day-Night v1.0",
        kind="module",
        entrypoint="python -m hloc.pipelines.Aachen.pipeline",
        default_dataset="./datasets/aachen",
        default_outputs="./outputs/aachen",
        prerequisites="Aachen Day-Night images, NVM/DB models, intrinsics, query lists, and the benchmark archive must already be present.",
        notes="Default route uses NetVLAD, SuperPoint Aachen, and SuperGlue; benchmark-scale run.",
        aliases=("aachen", "day-night", "aachen day night", "aachen day-night"),
        help_command="python -m hloc.pipelines.Aachen.pipeline --help",
    ),
    Entry(
        id="aachen-v1.1",
        title="Aachen Day-Night v1.1",
        kind="module",
        entrypoint="python -m hloc.pipelines.Aachen_v1_1.pipeline",
        default_dataset="./datasets/aachen_v1.1",
        default_outputs="./outputs/aachen_v1.1",
        prerequisites="Aachen v1.1 images, triangulated SIFT model, and query intrinsics must already be present.",
        notes="Default sparse route; the packaged workflow uses SuperPoint Max and SuperGlue.",
        aliases=("aachen v1.1", "aachen_v1.1", "aachen v1 1"),
        help_command="python -m hloc.pipelines.Aachen_v1_1.pipeline --help",
    ),
    Entry(
        id="aachen-v1.1-loftr",
        title="Aachen Day-Night v1.1 LoFTR",
        kind="module",
        entrypoint="python -m hloc.pipelines.Aachen_v1_1.pipeline_loftr",
        default_dataset="./datasets/aachen_v1.1",
        default_outputs="./outputs/aachen_v1.1",
        prerequisites="Same Aachen v1.1 dataset layout as the sparse route, plus dense-matching runtime support.",
        notes="Dense matching sibling of the v1.1 route; useful when a LoFTR-style pipeline is requested.",
        aliases=("loftr", "aachen loftr", "aachen v1.1 loftr"),
        help_command="python -m hloc.pipelines.Aachen_v1_1.pipeline_loftr --help",
    ),
    Entry(
        id="inloc-notebook",
        title="InLoc notebook workflow",
        kind="notebook",
        entrypoint="InLoc notebook workflow",
        default_dataset="./datasets/inloc",
        default_outputs="./outputs/inloc",
        prerequisites="InLoc benchmark images plus a precomputed NetVLAD top-40 retrieval file.",
        notes="Notebook/API route only; no 3D SfM model is needed and the plan should stay download-safe.",
        aliases=("inloc", "inloc notebook"),
    ),
    Entry(
        id="sfm-demo",
        title="SfM demo workflow",
        kind="notebook",
        entrypoint="SfM demo workflow",
        default_dataset="./datasets/sacre_coeur",
        default_outputs="./outputs/demo",
        prerequisites="A small local mapping image set; this is a tiny smoke or planning fixture, not a benchmark download.",
        notes="Notebook/API route only; good for a small reconstruction-and-localization smoke plan.",
        aliases=("sfm", "demo", "sacre coeur", "sacre_coeur"),
    ),
    Entry(
        id="4seasons-prepare-reference",
        title="4Seasons reference preparation",
        kind="module",
        entrypoint="python -m hloc.pipelines.4Seasons.prepare_reference",
        default_dataset="./datasets/4Seasons",
        default_outputs="./outputs/4Seasons",
        prerequisites="Reference sequence images, poses, intrinsics, and the challenge archive must already be unpacked.",
        notes="This step may delete unused images to speed extraction; work on a copy if you need to preserve the original files.",
        aliases=("4seasons", "4-seasons", "mlad"),
        help_command="python -m hloc.pipelines.4Seasons.prepare_reference --help",
    ),
    Entry(
        id="4seasons-localize",
        title="4Seasons relocalization",
        kind="module",
        entrypoint="python -m hloc.pipelines.4Seasons.localize",
        default_dataset="./datasets/4Seasons",
        default_outputs="./outputs/4Seasons",
        prerequisites="Chosen sequence images and the matching relocalization file must already be present.",
        notes="Training and validation sequences can be evaluated; test sequences only produce a submission bundle.",
        aliases=("4seasons localize", "4seasons relocalize"),
        help_command="python -m hloc.pipelines.4Seasons.localize --help",
    ),
    Entry(
        id="7scenes",
        title="7Scenes pipeline",
        kind="module",
        entrypoint="python -m hloc.pipelines.7Scenes.pipeline",
        default_dataset="./datasets/7scenes",
        default_outputs="./outputs/7scenes",
        prerequisites="Scene zips, triangulated SIFT models, DenseVLAD retrieval pairs, and optional rendered depth must already exist.",
        notes="Dense-depth mode is optional; use sparse mode if the depth archive is missing.",
        aliases=("7scenes", "7-scenes"),
        help_command="python -m hloc.pipelines.7Scenes.pipeline --help",
    ),
    Entry(
        id="cmu",
        title="Extended CMU Seasons pipeline",
        kind="module",
        entrypoint="python -m hloc.pipelines.CMU.pipeline",
        default_dataset="./datasets/cmu_extended",
        default_outputs="./outputs/aachen_extended",
        prerequisites="Root intrinsics plus per-slice database, query, sparse, and test-image files must already be unpacked.",
        notes="The packaged CLI keeps the historic output-root name `aachen_extended`; outputs are nested per slice.",
        aliases=("cmu", "extended cmu", "cmu seasons"),
        help_command="python -m hloc.pipelines.CMU.pipeline --help",
    ),
    Entry(
        id="cambridge",
        title="Cambridge Landmarks pipeline",
        kind="module",
        entrypoint="python -m hloc.pipelines.Cambridge.pipeline",
        default_dataset="./datasets/cambridge",
        default_outputs="./outputs/cambridge",
        prerequisites="Scene archives plus the retriangulated ground-truth model directory must already be present.",
        notes="Runs per scene and writes one results file per scene.",
        aliases=("cambridge", "cambridge landmarks"),
        help_command="python -m hloc.pipelines.Cambridge.pipeline --help",
    ),
    Entry(
        id="robotcar",
        title="RobotCar Seasons pipeline",
        kind="module",
        entrypoint="python -m hloc.pipelines.RobotCar.pipeline",
        default_dataset="./datasets/robotcar",
        default_outputs="./outputs/robotcar",
        prerequisites="Condition image zips, the three camera intrinsics files, and the NVM/reference database pair must already be present.",
        notes="Generates per-condition query lists and one combined results file.",
        aliases=("robotcar", "robotcar seasons"),
        help_command="python -m hloc.pipelines.RobotCar.pipeline --help",
    ),
)


def normalize(text: str) -> str:
    return " ".join(text.lower().replace("/", " ").replace("-", " ").replace("_", " ").split())


def selected_entries(filters: Iterable[str]) -> list[Entry]:
    cleaned = [normalize(token) for token in filters if normalize(token) and normalize(token) != "all"]
    if not cleaned:
        return list(ENTRIES)

    matches: list[Entry] = []
    for entry in ENTRIES:
        haystack = {
            normalize(entry.id),
            normalize(entry.title),
            normalize(entry.kind),
            normalize(entry.entrypoint),
            *(normalize(alias) for alias in entry.aliases),
        }
        if any(any(token in field or field in token for field in haystack) for token in cleaned):
            matches.append(entry)
    return matches


def render_plain(entries: list[Entry], show_help_commands: bool) -> None:
    for entry in entries:
        print(f"- {entry.id} ({entry.kind})")
        print(f"  title: {entry.title}")
        print(f"  entrypoint: {entry.entrypoint}")
        print(f"  dataset root: {entry.default_dataset}")
        print(f"  outputs: {entry.default_outputs}")
        print(f"  prerequisites: {entry.prerequisites}")
        print(f"  notes: {entry.notes}")
        if show_help_commands:
            print(f"  help command: {entry.help_command or 'n/a'}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List known Hierarchical-Localization dataset pipeline entrypoints without importing them.",
    )
    parser.add_argument(
        "--dataset",
        action="append",
        default=[],
        help=(
            "Filter by route alias or dataset name; repeat to include multiple routes. "
            "Use 'all' or omit the flag to list every entry."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON array instead of the plain-text summary.",
    )
    parser.add_argument(
        "--help-commands",
        action="store_true",
        help="Include safe --help command templates in the plain-text summary.",
    )
    args = parser.parse_args()

    entries = selected_entries(args.dataset)
    if not entries:
        parser.error("No known dataset pipeline entrypoints matched the requested filter.")

    if args.json:
        print(json.dumps([asdict(entry) for entry in entries], indent=2, sort_keys=True))
    else:
        render_plain(entries, args.help_commands)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
