#!/usr/bin/env python3
"""End-to-end tiny smoke for the OGB dataset export workflow."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import torch

from ogb.graphproppred import GraphPropPredDataset
from ogb.io import DatasetSaver


def build_graphs() -> list[dict[str, np.ndarray]]:
    return [
        {
            "edge_index": np.array([[0, 1], [1, 0]], dtype=np.int64),
            "num_nodes": 2,
            "node_feat": np.array([[1.0], [2.0]], dtype=np.float32),
            "edge_feat": np.array([[0.5], [0.5]], dtype=np.float32),
        },
        {
            "edge_index": np.array([[0, 2, 2], [2, 0, 1]], dtype=np.int64),
            "num_nodes": 3,
            "node_feat": np.array([[3.0], [4.0], [5.0]], dtype=np.float32),
            "edge_feat": np.array([[1.0], [1.0], [1.0]], dtype=np.float32),
        },
    ]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="ogb-datasetsaver-") as tmp:
        tmp_path = Path(tmp)
        saver = DatasetSaver("ogbg-toy", is_hetero=False, version=1, root=str(tmp_path / "submission"))
        saver.save_graph_list(build_graphs())
        saver.save_target_labels(np.array([[1], [0]], dtype=np.int64))
        saver.save_split(
            {
                "train": np.array([0], dtype=np.int64),
                "valid": np.array([1], dtype=np.int64),
                "test": np.array([1], dtype=np.int64),
            },
            split_name="toy-split",
        )

        mapping_dir = tmp_path / "mapping"
        mapping_dir.mkdir()
        (mapping_dir / "README.md").write_text("Toy mapping for the OGB dataset export smoke.\n", encoding="utf-8")
        saver.copy_mapping_dir(str(mapping_dir))
        saver.save_task_info(task_type="classification", eval_metric="acc", num_classes=2)
        meta_dict = saver.get_meta_dict()
        saver.zip()

        dataset = GraphPropPredDataset("ogbg-toy", meta_dict=meta_dict)
        graph, label = dataset[0]
        print("len:", len(dataset))
        print("graph_num_nodes:", graph["num_nodes"])
        print("label_shape:", label.shape)

        split_path = tmp_path / "submission_ogbg_toy" / "toy" / "split" / "toy-split" / "split_dict.pt"
        split_dict = torch.load(split_path, weights_only=False)
        print("split_keys:", sorted(split_dict.keys()))

        saver.cleanup()


if __name__ == "__main__":
    main()
