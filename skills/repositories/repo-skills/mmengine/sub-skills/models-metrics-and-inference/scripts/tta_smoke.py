#!/usr/bin/env python3
"""Tiny MMEngine BaseTTAModel smoke check.

This adapts MMEngine's documented classification TTA merge pattern to tiny local
objects. It uses no downstream task package, remote weights, datasets, or Runner.
"""

from __future__ import annotations

import argparse


def run_smoke(verbose: bool = False) -> None:
    try:
        import torch
        from mmengine.model import BaseModel, BaseTTAModel
        from mmengine.structures import BaseDataElement
    except ImportError as exc:
        raise SystemExit(
            "Missing runtime dependency for this smoke check. Install MMEngine "
            "with PyTorch, then rerun this script. "
            f"Original import error: {exc}") from exc

    class TinyClsSample(BaseDataElement):
        def set_pred_score(self, score):
            self.pred_score = score
            return self

        def set_pred_label(self, label):
            self.pred_label = label
            return self

    class TinyClassifier(BaseModel):
        def __init__(self):
            super().__init__()
            self.bias = torch.nn.Parameter(torch.tensor(0.0))

        def forward(self, inputs, data_samples=None, mode="tensor"):
            if mode == "tensor":
                return inputs + self.bias
            if mode == "predict":
                return self._predict(inputs, data_samples)
            if mode == "loss":
                return {"loss_dummy": (inputs + self.bias).sum() * 0}
            raise RuntimeError(f"Invalid mode: {mode}")

        def test_step(self, data):
            if isinstance(data, dict):
                inputs = data["inputs"]
                data_samples = data.get("data_samples")
            elif isinstance(data, (tuple, list)):
                inputs = data[0]
                data_samples = data[1] if len(data) > 1 else None
            else:
                raise TypeError(f"Unsupported data batch type: {type(data)}")
            return self._predict(inputs, data_samples)

        def _predict(self, inputs, data_samples=None):
            predictions = []
            for value, sample in zip(inputs, data_samples or [None] * len(inputs)):
                base = sample.new() if isinstance(sample, BaseDataElement) else TinyClsSample()
                score = torch.stack([1 - value.float(), value.float()])
                predictions.append(
                    base.set_pred_score(score).set_pred_label(int(score.argmax().item())))
            return predictions

    class AverageScoreTTA(BaseTTAModel):
        def merge_preds(self, data_samples_list):
            merged = []
            for augmented_predictions in data_samples_list:
                result = augmented_predictions[0].new()
                score = sum(sample.pred_score for sample in augmented_predictions) / len(augmented_predictions)
                result.set_pred_score(score)
                result.set_pred_label(int(score.argmax().item()))
                merged.append(result)
            return merged

    model = TinyClassifier()
    tta_model = AverageScoreTTA(model)
    batch = {
        "inputs": [
            [torch.tensor(0.20), torch.tensor(0.75)],
            [torch.tensor(0.40), torch.tensor(0.55)],
        ],
        "data_samples": [
            [TinyClsSample(sample_id="a", aug="low"), TinyClsSample(sample_id="b", aug="high")],
            [TinyClsSample(sample_id="a", aug="mid"), TinyClsSample(sample_id="b", aug="mid")],
        ],
    }

    merged = tta_model.test_step(batch)
    assert len(merged) == 2
    assert [sample.pred_label for sample in merged] == [0, 1]
    assert torch.allclose(merged[0].pred_score, torch.tensor([0.70, 0.30]))
    assert torch.allclose(merged[1].pred_score, torch.tensor([0.35, 0.65]))

    tuple_batch = (
        [[torch.tensor(0.10), torch.tensor(0.60)], [torch.tensor(0.30), torch.tensor(0.80)]],
        [[TinyClsSample(), TinyClsSample()], [TinyClsSample(), TinyClsSample()]],
    )
    tuple_merged = tta_model.test_step(tuple_batch)
    assert len(tuple_merged) == 2
    assert [sample.pred_label for sample in tuple_merged] == [0, 1]

    if verbose:
        print(f"dict_labels={[sample.pred_label for sample in merged]}")
        print(f"dict_scores={[sample.pred_score.tolist() for sample in merged]}")
        print(f"tuple_labels={[sample.pred_label for sample in tuple_merged]}")

    print("MMEngine TTA smoke passed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny CPU-only smoke check for MMEngine BaseTTAModel "
            "test_step and merge_preds contracts."))
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print validated TTA merge details.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_smoke(verbose=args.verbose)


if __name__ == "__main__":
    main()
