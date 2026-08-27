#!/usr/bin/env python3
"""Tiny MMEngine model, metric, evaluator, and analysis smoke check.

This script uses only CPU tensors and temporary local files. It validates a
minimal BaseModel/BaseModule contract, ImgDataPreprocessor behavior,
BaseMetric/Evaluator prefixing, DumpResults output, and model complexity APIs.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path


def run_smoke(verbose: bool = False) -> None:
    try:
        import torch
        import torch.nn as nn
        from mmengine.analysis import get_model_complexity_info
        from mmengine.evaluator import BaseMetric, DumpResults, Evaluator
        from mmengine.fileio import load
        from mmengine.model import BaseModel, BaseModule, ImgDataPreprocessor
        from mmengine.optim import OptimWrapper
    except ImportError as exc:
        raise SystemExit(
            "Missing runtime dependency for this smoke check. Install MMEngine "
            "with PyTorch, then rerun this script. "
            f"Original import error: {exc}") from exc

    class TinyHead(BaseModule):
        def __init__(self, init_cfg=None):
            super().__init__(init_cfg=init_cfg)
            self.linear = nn.Linear(4, 2)

        def forward(self, inputs):
            return self.linear(inputs.flatten(1))

    class TinyModel(BaseModel):
        def __init__(self, data_preprocessor=None):
            super().__init__(data_preprocessor=data_preprocessor)
            self.head = TinyHead()
            self.loss_fn = nn.CrossEntropyLoss()

        def forward(self, inputs, data_samples=None, mode="tensor"):
            logits = self.head(inputs)
            if mode == "loss":
                labels = torch.tensor(
                    [sample["gt_label"] for sample in data_samples],
                    dtype=torch.long,
                    device=logits.device,
                )
                return {"loss_cls": self.loss_fn(logits, labels)}
            if mode == "predict":
                scores = torch.softmax(logits, dim=1)
                labels = scores.argmax(dim=1)
                return [
                    {
                        "pred_label": int(label.item()),
                        "gt_label": int(sample["gt_label"]),
                        "score": float(score[label].item()),
                    }
                    for label, score, sample in zip(labels, scores, data_samples)
                ]
            if mode == "tensor":
                return logits
            raise RuntimeError(f"Invalid mode: {mode}")

    class TinyAccuracy(BaseMetric):
        default_prefix = "tiny"

        def process(self, data_batch, data_samples):
            for sample in data_samples:
                self.results.append(
                    {
                        "pred": int(sample["pred_label"]),
                        "target": int(sample["gt_label"]),
                    })

        def compute_metrics(self, results):
            correct = sum(item["pred"] == item["target"] for item in results)
            return {"accuracy": correct / max(len(results), 1), "count": len(results)}

    batch = {
        "inputs": [
            torch.tensor([[[0.0, 1.0], [2.0, 3.0]]]),
            torch.tensor([[[4.0, 5.0], [6.0, 7.0]]]),
        ],
        "data_samples": [{"gt_label": 0}, {"gt_label": 1}],
    }
    data_preprocessor = ImgDataPreprocessor(mean=[0.0], std=[1.0], pad_size_divisor=1)
    processed = data_preprocessor(batch, training=True)
    assert tuple(processed["inputs"].shape) == (2, 1, 2, 2)

    model = TinyModel(data_preprocessor=data_preprocessor)
    tensor_output = model.forward(
        processed["inputs"], processed["data_samples"], mode="tensor")
    assert tuple(tensor_output.shape) == (2, 2)

    loss_output = model.forward(
        processed["inputs"], processed["data_samples"], mode="loss")
    parsed_loss, log_vars = model.parse_losses(loss_output)
    assert parsed_loss.ndim == 0
    assert "loss" in log_vars and "loss_cls" in log_vars

    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    optim_wrapper = OptimWrapper(optimizer)
    log_vars = model.train_step(batch, optim_wrapper)
    assert "loss" in log_vars

    predictions = model.test_step(batch)
    assert isinstance(predictions, list)
    assert len(predictions) == 2
    assert {"pred_label", "gt_label", "score"}.issubset(predictions[0])

    evaluator = Evaluator(TinyAccuracy())
    evaluator.process(data_samples=predictions, data_batch=batch)
    metrics = evaluator.evaluate(size=len(predictions))
    assert set(metrics) == {"tiny/accuracy", "tiny/count"}
    assert metrics["tiny/count"] == 2
    assert evaluator.metrics[0].results == []

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        dump_path = Path(tmp_dir_name) / "predictions.pkl"
        dump_metric = DumpResults(out_file_path=str(dump_path))
        dump_metric.process(None, predictions)
        dump_metric.compute_metrics(dump_metric.results)
        dumped = load(dump_path)
        assert dumped == predictions

    complexity = get_model_complexity_info(
        model.head,
        inputs=torch.randn(1, 1, 2, 2),
        show_table=False,
        show_arch=False,
    )
    for key in ("flops", "flops_str", "params", "params_str"):
        assert key in complexity

    if verbose:
        print(f"processed_shape={tuple(processed['inputs'].shape)}")
        print(f"prediction_keys={sorted(predictions[0])}")
        print(f"metrics={metrics}")
        print(f"complexity={{'flops': {complexity['flops']}, 'params': {complexity['params']}}}")

    print("MMEngine model/metric smoke passed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny CPU-only smoke check for MMEngine BaseModel, "
            "BaseModule, data preprocessor, metric/evaluator, DumpResults, "
            "and model complexity contracts."))
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print validated mini contract details.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_smoke(verbose=args.verbose)


if __name__ == "__main__":
    main()
