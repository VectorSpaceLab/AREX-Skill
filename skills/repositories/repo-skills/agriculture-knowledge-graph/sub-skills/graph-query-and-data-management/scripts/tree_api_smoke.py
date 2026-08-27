#!/usr/bin/env python3
"""Self-contained smoke check for Agriculture_KnowledgeGraph TREE behavior.

The original repository defines a TREE class in its toolkit. This script mirrors
only the small hierarchy-loading and traversal contract needed for runtime skill
verification. It creates temporary edge/leaf files, reads them, and asserts
TREE-like behavior without importing or reading the original checkout.
"""

from __future__ import annotations

import argparse
import random
import tempfile
from pathlib import Path
from typing import Dict, List


class TinyTree:
    """Small source-compatible subset of the repository's TREE class."""

    root = "农业"

    def __init__(self) -> None:
        self.edge: Dict[str, List[str]] = {}
        self.leaf: Dict[str, List[str]] = {}
        self.curpath: List[str] = []
        self.anspath: List[List[str]] = []
        self.ui_str = ""

    def read_edge(self, src: Path) -> None:
        self.edge = {}
        seen = set()
        with src.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line in seen:
                    continue
                seen.add(line)
                parts = line.strip().split(" ")
                if len(parts) < 2:
                    raise ValueError(f"malformed edge line: {line!r}")
                parent, child = parts[0], parts[1]
                self.edge.setdefault(parent, []).append(child)

    def read_leaf(self, src: Path) -> None:
        self.leaf = {}
        seen = set()
        with src.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line in seen:
                    continue
                seen.add(line)
                parts = line.strip().split(" ")
                if len(parts) < 2:
                    raise ValueError(f"malformed leaf line: {line!r}")
                category, entity = parts[0], parts[1]
                self.leaf.setdefault(category, []).append(entity)

    def _dfs(self, word: str, node: str) -> None:
        self.curpath.append(node)
        if node in self.leaf and word in self.leaf[node]:
            self.anspath.append([*self.curpath, word])
        for child in self.edge.get(node, []):
            self._dfs(word, child)
        self.curpath.pop()

    def get_path(self, word: str, unique: bool) -> List[List[str]]:
        self.anspath = []
        self.curpath = []
        self._dfs(word, self.root)
        random.shuffle(self.anspath)
        if unique:
            i = 0
            while i < len(self.anspath):
                j = i + 1
                while j < len(self.anspath):
                    if len(set(self.anspath[i]) & set(self.anspath[j])) > 2:
                        del self.anspath[j]
                    else:
                        j += 1
                i += 1
        return self.anspath

    def get_father(self, word: str) -> List[str]:
        return [parent for parent, children in self.edge.items() if word in children]

    def get_branch(self, word: str) -> List[str]:
        return list(self.edge.get(word, []))

    def get_leaf(self, word: str) -> List[str]:
        return list(self.leaf.get(word, []))

    def _dfs_to_theme(self, theme: str, node: str) -> None:
        if self.anspath and self.anspath[-1] == theme:  # type: ignore[comparison-overlap]
            return
        # The original stores this one UI path as a flat list in anspath.
        self.anspath.append(node)  # type: ignore[arg-type]
        for child in self.edge.get(node, []):
            self._dfs_to_theme(theme, child)
        if self.anspath and self.anspath[-1] == theme:  # type: ignore[comparison-overlap]
            return
        self.anspath.pop()

    def _dfs_create_ui(self, node: str, depth: int) -> None:
        active_path = self.anspath  # flat list during UI generation
        visible = len(active_path) > depth and node == active_path[depth]
        self.ui_str += " <li> <span>" if visible else ' <li style="display: none;"> <span>'
        if node in self.edge and self.edge[node]:
            if visible and len(active_path) != depth + 1:
                self.ui_str += '<i class="fa fa-minus-square" aria-hidden="true"></i>&nbsp;'
            else:
                self.ui_str += '<i class="fa fa-plus-square" aria-hidden="true"></i>&nbsp;'
        self.ui_str += f"{node}</span>"
        if active_path and node == active_path[-1]:
            self.ui_str += "&nbsp;&nbsp;&nbsp;当前分类"
        else:
            self.ui_str += f'&nbsp;<a href="overview?node={node}">&nbsp;&nbsp;[进入分类]</a>'
        if node in self.edge and self.edge[node]:
            self.ui_str += "<ul>"
            for child in self.edge[node]:
                self._dfs_create_ui(child, depth + 1)
            self.ui_str += "</ul>"
        self.ui_str += "</li>"

    def create_UI(self, theme: str) -> str:
        self.anspath = []  # type: ignore[assignment]
        self._dfs_to_theme(theme, self.root)
        self.ui_str = "<ul>"
        self._dfs_create_ui(self.root, 0)
        self.ui_str += "</ul>"
        return self.ui_str


def write_fixture(directory: Path) -> tuple[Path, Path]:
    edge_path = directory / "micropedia_tree.txt"
    leaf_path = directory / "leaf_list.txt"
    edge_path.write_text(
        "\n".join(
            [
                "农业 可以食用的植物",
                "可以食用的植物 粮食作物",
                "粮食作物 谷物",
                "粮食作物 谷物",  # duplicate should be ignored
                "农业 经济作物",
                "经济作物 油料作物",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    leaf_path.write_text(
        "\n".join(
            [
                "谷物 小麦",
                "谷物 水稻",
                "谷物 小麦",  # duplicate should be ignored
                "油料作物 花生",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return edge_path, leaf_path


def run_smoke(verbose: bool = False) -> None:
    with tempfile.TemporaryDirectory(prefix="agri_tree_smoke_") as tmp:
        fixture_dir = Path(tmp)
        edge_path, leaf_path = write_fixture(fixture_dir)
        tree = TinyTree()
        tree.read_edge(edge_path)
        tree.read_leaf(leaf_path)

        expected_path = ["农业", "可以食用的植物", "粮食作物", "谷物", "小麦"]
        assert tree.get_path("小麦", unique=False) == [expected_path]
        assert tree.get_path("不存在", unique=False) == []
        assert tree.get_father("谷物") == ["粮食作物"]
        assert tree.get_branch("可以食用的植物") == ["粮食作物"]
        assert tree.get_leaf("谷物") == ["小麦", "水稻"]

        ui = tree.create_UI("谷物")
        assert ui.startswith("<ul>") and ui.endswith("</ul>")
        assert "当前分类" in ui
        assert "粮食作物" in ui

        if verbose:
            print(f"fixture_dir={fixture_dir}")
            print(f"path={expected_path}")
            print(f"ui_prefix={ui[:120]}")

    print("tree_api_smoke: OK")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a self-contained tiny-fixture smoke check for TREE-like hierarchy behavior."
    )
    parser.add_argument("--verbose", action="store_true", help="Print fixture details and UI prefix.")
    args = parser.parse_args()
    run_smoke(verbose=args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
