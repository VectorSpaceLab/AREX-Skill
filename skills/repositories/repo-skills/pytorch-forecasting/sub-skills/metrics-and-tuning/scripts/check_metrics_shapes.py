#!/usr/bin/env python3
"""Check PyTorch Forecasting metric/loss tensor shape contracts without training.

The script constructs tiny synthetic tensors and runs selected metric/loss methods.
It does not build datasets, dataloaders, models, trainers, or checkpoints.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from typing import Any


CASES = (
    "point",
    "quantile",
    "classification",
    "mase",
    "composite",
    "aggregate",
    "multiloss",
    "distribution",
    "optional",
    "all",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Construct synthetic tensors and validate PyTorch Forecasting metric/loss shapes without training.",
    )
    parser.add_argument(
        "--case",
        choices=CASES,
        default="all",
        help="Shape-check family to run. 'all' runs every non-training check.",
    )
    parser.add_argument("--batch-size", type=int, default=3, help="Synthetic batch size.")
    parser.add_argument("--horizon", type=int, default=4, help="Synthetic prediction horizon.")
    parser.add_argument(
        "--encoder-length",
        type=int,
        default=6,
        help="Synthetic encoder length for MASE checks.",
    )
    parser.add_argument(
        "--classes",
        type=int,
        default=5,
        help="Number of classes for CrossEntropy checks.",
    )
    parser.add_argument(
        "--quantiles",
        type=float,
        nargs="+",
        default=[0.1, 0.5, 0.9],
        help="Quantile levels for QuantileLoss and distribution to_quantiles checks.",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="cpu",
        help="Device for synthetic tensors. No training is run.",
    )
    parser.add_argument(
        "--seed", type=int, default=13, help="Torch random seed for synthetic tensors."
    )
    return parser.parse_args()


def shape(value: Any) -> Any:
    """Return a JSON-friendly shape description."""
    if isinstance(value, list):
        return [shape(v) for v in value]
    if hasattr(value, "shape"):
        return list(value.shape)
    return str(value)


def assert_shape(actual: Any, expected: list[int] | tuple[int, ...], label: str) -> None:
    got = list(actual.shape)
    exp = list(expected)
    if got != exp:
        raise AssertionError(f"{label}: expected shape {exp}, got {got}")


def assert_scalar(tensor: Any, label: str) -> None:
    if getattr(tensor, "ndim", None) != 0:
        raise AssertionError(f"{label}: expected scalar tensor, got shape {shape(tensor)}")


def validate_args(args: argparse.Namespace) -> None:
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be positive")
    if args.horizon <= 0:
        raise ValueError("--horizon must be positive")
    if args.encoder_length <= 0:
        raise ValueError("--encoder-length must be positive")
    if args.classes <= 1:
        raise ValueError("--classes must be greater than 1")
    if not args.quantiles:
        raise ValueError("--quantiles must contain at least one value")
    bad = [q for q in args.quantiles if not 0 < q < 1]
    if bad:
        raise ValueError(f"quantiles must be in (0, 1), got {bad}")


def import_runtime():
    try:
        import torch
        from pytorch_forecasting.metrics import (
            MAE,
            MAPE,
            MASE,
            RMSE,
            SMAPE,
            BetaDistributionLoss,
            CrossEntropy,
            ImplicitQuantileNetworkDistributionLoss,
            LogNormalDistributionLoss,
            MultivariateNormalDistributionLoss,
            NegativeBinomialDistributionLoss,
            NormalDistributionLoss,
            QuantileLoss,
            MultiLoss,
        )
        from pytorch_forecasting.metrics.base_metrics import AggregationMetric
    except Exception as exc:  # pragma: no cover - user environment diagnostic
        raise RuntimeError(
            "Could not import torch and pytorch_forecasting metrics. Install the base "
            "pytorch-forecasting package before running shape checks."
        ) from exc

    return {
        "torch": torch,
        "SMAPE": SMAPE,
        "MAE": MAE,
        "MAPE": MAPE,
        "RMSE": RMSE,
        "MASE": MASE,
        "CrossEntropy": CrossEntropy,
        "QuantileLoss": QuantileLoss,
        "NormalDistributionLoss": NormalDistributionLoss,
        "NegativeBinomialDistributionLoss": NegativeBinomialDistributionLoss,
        "LogNormalDistributionLoss": LogNormalDistributionLoss,
        "BetaDistributionLoss": BetaDistributionLoss,
        "MultivariateNormalDistributionLoss": MultivariateNormalDistributionLoss,
        "ImplicitQuantileNetworkDistributionLoss": ImplicitQuantileNetworkDistributionLoss,
        "MultiLoss": MultiLoss,
        "AggregationMetric": AggregationMetric,
    }


def select_device(torch, requested: str) -> str:
    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("--device cuda requested but torch.cuda.is_available() is false")
    return requested


def run_point(rt, args, device: str) -> list[dict[str, Any]]:
    torch = rt["torch"]
    target = torch.rand(args.batch_size, args.horizon, device=device) + 0.1
    pred = torch.rand(args.batch_size, args.horizon, device=device) + 0.1
    out = []
    for name in ("SMAPE", "MAE", "MAPE", "RMSE"):
        metric = rt[name]()
        scalar = metric(pred, target)
        assert_scalar(scalar, name)
        none_metric = rt[name](reduction="none")
        matrix = none_metric(pred, target)
        assert_shape(matrix, [args.batch_size, args.horizon], f"{name} reduction=none")
        out.append(
            {
                "case": "point",
                "metric": name,
                "scalar_shape": shape(scalar),
                "none_shape": shape(matrix),
            }
        )
    return out


def run_quantile(rt, args, device: str) -> list[dict[str, Any]]:
    torch = rt["torch"]
    target = torch.rand(args.batch_size, args.horizon, device=device)
    offsets = torch.linspace(-0.2, 0.2, len(args.quantiles), device=device)
    pred = target.unsqueeze(-1) + offsets
    loss = rt["QuantileLoss"](quantiles=list(args.quantiles))

    raw = loss.loss(pred, target)
    scalar = loss(pred, target)
    point = loss.to_prediction(pred)
    quantiles = loss.to_quantiles(pred)

    assert_shape(raw, [args.batch_size, args.horizon, len(args.quantiles)], "QuantileLoss.loss")
    assert_scalar(scalar, "QuantileLoss")
    assert_shape(point, [args.batch_size, args.horizon], "QuantileLoss.to_prediction")
    assert_shape(quantiles, [args.batch_size, args.horizon, len(args.quantiles)], "QuantileLoss.to_quantiles")
    return [
        {
            "case": "quantile",
            "metric": "QuantileLoss",
            "input_shape": shape(pred),
            "target_shape": shape(target),
            "loss_shape": shape(raw),
            "scalar_shape": shape(scalar),
            "point_shape": shape(point),
            "quantile_shape": shape(quantiles),
        }
    ]


def run_classification(rt, args, device: str) -> list[dict[str, Any]]:
    torch = rt["torch"]
    logits = torch.randn(args.batch_size, args.horizon, args.classes, device=device)
    target = torch.randint(0, args.classes, (args.batch_size, args.horizon), device=device)
    loss = rt["CrossEntropy"]()
    scalar = loss(logits, target)
    labels = loss.to_prediction(logits)
    assert_scalar(scalar, "CrossEntropy")
    assert_shape(labels, [args.batch_size, args.horizon], "CrossEntropy.to_prediction")
    if labels.dtype != torch.long:
        raise AssertionError(f"CrossEntropy.to_prediction expected torch.long, got {labels.dtype}")
    return [
        {
            "case": "classification",
            "metric": "CrossEntropy",
            "logits_shape": shape(logits),
            "target_shape": shape(target),
            "label_shape": shape(labels),
            "label_dtype": str(labels.dtype),
        }
    ]


def run_mase(rt, args, device: str) -> list[dict[str, Any]]:
    torch = rt["torch"]
    pred = torch.rand(args.batch_size, args.horizon, device=device)
    decoder_target = torch.rand(args.batch_size, args.horizon, device=device)
    encoder_target = torch.rand(args.batch_size, args.encoder_length, device=device)
    encoder_lengths = torch.full(
        (args.batch_size,), args.encoder_length, dtype=torch.long, device=device
    )
    decoder_lengths = torch.full(
        (args.batch_size,), args.horizon, dtype=torch.long, device=device
    )
    metric = rt["MASE"]()
    metric.update(pred, decoder_target, encoder_target, encoder_lengths)
    scalar = metric.compute()
    scaling = rt["MASE"].calculate_scaling(
        decoder_target, decoder_lengths, encoder_target, encoder_lengths
    )
    assert_scalar(scalar, "MASE.compute")
    assert_shape(scaling, [args.batch_size], "MASE.calculate_scaling")
    return [
        {
            "case": "mase",
            "metric": "MASE",
            "prediction_shape": shape(pred),
            "encoder_target_shape": shape(encoder_target),
            "scaling_shape": shape(scaling),
            "scalar_shape": shape(scalar),
        }
    ]


def run_composite(rt, args, device: str) -> list[dict[str, Any]]:
    torch = rt["torch"]
    target = torch.rand(args.batch_size, args.horizon, device=device) + 0.1
    pred = torch.rand(args.batch_size, args.horizon, device=device) + 0.1
    metric = rt["SMAPE"]() + 1e-4 * rt["MAE"]()
    scalar = metric(pred, target)
    point = metric.to_prediction(pred)
    quantiles = metric.to_quantiles(pred)
    assert_scalar(scalar, "CompositeMetric")
    assert_shape(point, [args.batch_size, args.horizon], "CompositeMetric.to_prediction")
    assert_shape(quantiles, [args.batch_size, args.horizon, 1], "CompositeMetric.to_quantiles")
    return [
        {
            "case": "composite",
            "metric": "SMAPE + 1e-4 * MAE",
            "scalar_shape": shape(scalar),
            "point_shape": shape(point),
            "quantile_shape": shape(quantiles),
        }
    ]


def run_aggregate(rt, args, device: str) -> list[dict[str, Any]]:
    torch = rt["torch"]
    target = torch.rand(args.batch_size, args.horizon, device=device)
    pred = torch.rand(args.batch_size, args.horizon, device=device)
    metric = rt["AggregationMetric"](
        metric=rt["MAE"](),
    )
    scalar = metric(pred, target)
    assert_scalar(scalar, "AggregationMetric")
    return [
        {
            "case": "aggregate",
            "metric": "AggregationMetric(MAE)",
            "prediction_shape": shape(pred),
            "target_shape": shape(target),
            "scalar_shape": shape(scalar),
        }
    ]


def run_multiloss(rt, args, device: str) -> list[dict[str, Any]]:
    torch = rt["torch"]
    target_a = torch.rand(args.batch_size, args.horizon, device=device) + 0.1
    target_b = torch.rand(args.batch_size, args.horizon, device=device)
    pred_a = torch.rand(args.batch_size, args.horizon, device=device) + 0.1
    pred_b = target_b.unsqueeze(-1) + torch.linspace(
        -0.2, 0.2, len(args.quantiles), device=device
    )
    quantile_loss = rt["QuantileLoss"](quantiles=list(args.quantiles))
    loss = rt["MultiLoss"]([rt["MAE"](), quantile_loss], weights=[1.0, 0.5])
    scalar = loss([pred_a, pred_b], ([target_a, target_b], None))
    points = loss.to_prediction([pred_a, pred_b])
    quantiles = loss.to_quantiles([pred_a, pred_b])
    assert_scalar(scalar, "MultiLoss")
    assert_shape(points[0], [args.batch_size, args.horizon], "MultiLoss point target point")
    assert_shape(points[1], [args.batch_size, args.horizon], "MultiLoss quantile target point")
    assert_shape(quantiles[0], [args.batch_size, args.horizon, 1], "MultiLoss first quantiles")
    assert_shape(
        quantiles[1],
        [args.batch_size, args.horizon, len(args.quantiles)],
        "MultiLoss second quantiles",
    )
    return [
        {
            "case": "multiloss",
            "metric": "MultiLoss([MAE, QuantileLoss])",
            "scalar_shape": shape(scalar),
            "point_shapes": shape(points),
            "quantile_shapes": shape(quantiles),
        }
    ]


def run_distribution(rt, args, device: str) -> list[dict[str, Any]]:
    torch = rt["torch"]
    batch = args.batch_size
    horizon = args.horizon
    q_count = len(args.quantiles)
    results = []

    target_real = torch.randn(batch, horizon, device=device)
    normal_params = torch.stack(
        [
            torch.zeros(batch, horizon, device=device),
            torch.ones(batch, horizon, device=device),
            torch.zeros(batch, horizon, device=device),
            torch.ones(batch, horizon, device=device),
        ],
        dim=-1,
    )
    normal = rt["NormalDistributionLoss"](quantiles=list(args.quantiles))
    # rescale_parameters() normally sets this; direct synthetic checks mimic no transform.
    normal._transformation = None
    raw = normal.loss(normal_params, target_real)
    point = normal.to_prediction(normal_params, n_samples=8)
    quant = normal.to_quantiles(normal_params, quantiles=list(args.quantiles), n_samples=8)
    assert_shape(raw, [batch, horizon], "NormalDistributionLoss.loss")
    assert_shape(point, [batch, horizon], "NormalDistributionLoss.to_prediction")
    assert_shape(quant, [batch, horizon, q_count], "NormalDistributionLoss.to_quantiles")
    results.append(
        {
            "case": "distribution",
            "metric": "NormalDistributionLoss",
            "parameter_shape_used_for_loss": shape(normal_params),
            "loss_shape": shape(raw),
            "point_shape": shape(point),
            "quantile_shape": shape(quant),
        }
    )

    count_target = torch.poisson(torch.full((batch, horizon), 4.0, device=device))
    nb_params = torch.stack(
        [
            torch.full((batch, horizon), 4.0, device=device),
            torch.full((batch, horizon), 1.5, device=device),
        ],
        dim=-1,
    )
    nb = rt["NegativeBinomialDistributionLoss"]()
    nb_loss = nb.loss(nb_params, count_target)
    assert_shape(nb_loss, [batch, horizon], "NegativeBinomialDistributionLoss.loss")
    results.append(
        {
            "case": "distribution",
            "metric": "NegativeBinomialDistributionLoss",
            "parameter_shape_used_for_loss": shape(nb_params),
            "loss_shape": shape(nb_loss),
        }
    )

    positive_target = torch.rand(batch, horizon, device=device) + 0.1
    lognormal_params = torch.stack(
        [
            torch.zeros(batch, horizon, device=device),
            torch.ones(batch, horizon, device=device),
        ],
        dim=-1,
    )
    lognormal = rt["LogNormalDistributionLoss"]()
    lognormal_loss = lognormal.loss(lognormal_params, positive_target)
    assert_shape(lognormal_loss, [batch, horizon], "LogNormalDistributionLoss.loss")
    results.append(
        {
            "case": "distribution",
            "metric": "LogNormalDistributionLoss",
            "parameter_shape_used_for_loss": shape(lognormal_params),
            "loss_shape": shape(lognormal_loss),
        }
    )

    beta_target = torch.rand(batch, horizon, device=device) * 0.8 + 0.1
    beta_params = torch.stack(
        [
            torch.full((batch, horizon), 0.5, device=device),
            torch.full((batch, horizon), 5.0, device=device),
        ],
        dim=-1,
    )
    beta = rt["BetaDistributionLoss"]()
    beta_loss = beta.loss(beta_params, beta_target)
    assert_shape(beta_loss, [batch, horizon], "BetaDistributionLoss.loss")
    results.append(
        {
            "case": "distribution",
            "metric": "BetaDistributionLoss",
            "parameter_shape_used_for_loss": shape(beta_params),
            "loss_shape": shape(beta_loss),
        }
    )

    iqn = rt["ImplicitQuantileNetworkDistributionLoss"](
        quantiles=list(args.quantiles), input_size=5, hidden_size=8, n_loss_samples=8
    ).to(device)
    # rescale_parameters() normally sets this; direct synthetic checks mimic no transform.
    iqn._transformation = None
    iqn_params = torch.randn(batch, horizon, 7, device=device)
    iqn_params[..., -2] = 0.0  # loc
    iqn_params[..., -1] = 1.0  # scale
    iqn_loss = iqn.loss(iqn_params, target_real)
    iqn_quantiles = iqn.to_quantiles(iqn_params, quantiles=list(args.quantiles))
    iqn_point = iqn.to_prediction(iqn_params, n_samples=None)
    assert_shape(iqn_loss, [batch, horizon], "ImplicitQuantileNetworkDistributionLoss.loss")
    assert_shape(iqn_quantiles, [batch, horizon, q_count], "ImplicitQuantileNetworkDistributionLoss.to_quantiles")
    assert_shape(iqn_point, [batch, horizon], "ImplicitQuantileNetworkDistributionLoss.to_prediction")
    results.append(
        {
            "case": "distribution",
            "metric": "ImplicitQuantileNetworkDistributionLoss",
            "parameter_shape_used_for_loss": shape(iqn_params),
            "loss_shape": shape(iqn_loss),
            "point_shape": shape(iqn_point),
            "quantile_shape": shape(iqn_quantiles),
        }
    )

    mv = rt["MultivariateNormalDistributionLoss"](rank=1, quantiles=list(args.quantiles))
    # rescale_parameters() normally sets this; direct synthetic checks mimic no transform.
    mv._transformation = None
    mv_params = torch.zeros(batch, horizon, 5, device=device)
    mv_params[..., 0] = 0.0  # target-scale loc
    mv_params[..., 1] = 1.0  # target-scale scale
    mv_params[..., 2] = 0.0  # distribution loc
    mv_params[..., 3] = 0.2  # positive covariance diagonal
    mv_params[..., 4] = 0.0  # covariance factor
    mv_loss = mv.loss(mv_params, target_real)
    assert_scalar(mv_loss, "MultivariateNormalDistributionLoss.loss")
    results.append(
        {
            "case": "distribution",
            "metric": "MultivariateNormalDistributionLoss",
            "parameter_shape_used_for_loss": shape(mv_params),
            "loss_shape": shape(mv_loss),
            "note": "multivariate loss is scalar over the event, unlike ordinary per-horizon distribution losses",
        }
    )

    return results


def run_optional(rt, args, device: str) -> list[dict[str, Any]]:
    del rt, args, device
    cpflows_available = importlib.util.find_spec("cpflows") is not None
    optuna_available = importlib.util.find_spec("optuna") is not None
    optuna_integration_available = importlib.util.find_spec("optuna_integration") is not None
    statsmodels_available = importlib.util.find_spec("statsmodels") is not None
    matplotlib_available = importlib.util.find_spec("matplotlib") is not None
    return [
        {
            "case": "optional",
            "feature": "MQF2DistributionLoss",
            "available": cpflows_available,
            "required_package": "cpflows",
            "install_hint": "pip install \"pytorch-forecasting[mqf2]\"",
        },
        {
            "case": "optional",
            "feature": "optimize_hyperparameters",
            "available": optuna_available
            and optuna_integration_available
            and statsmodels_available,
            "packages": {
                "optuna": optuna_available,
                "optuna_integration": optuna_integration_available,
                "statsmodels": statsmodels_available,
            },
            "install_hint": "pip install \"pytorch-forecasting[tuning]\"",
        },
        {
            "case": "optional",
            "feature": "LR finder plotting",
            "available": matplotlib_available,
            "required_package": "matplotlib",
            "install_hint": "Install matplotlib or use res.suggestion() without plotting.",
        },
    ]


def cases_to_run(selected: str) -> list[str]:
    if selected == "all":
        return [case for case in CASES if case != "all"]
    return [selected]


def main() -> int:
    args = parse_args()
    validate_args(args)
    rt = import_runtime()
    torch = rt["torch"]
    device = select_device(torch, args.device)
    torch.manual_seed(args.seed)

    runners = {
        "point": run_point,
        "quantile": run_quantile,
        "classification": run_classification,
        "mase": run_mase,
        "composite": run_composite,
        "aggregate": run_aggregate,
        "multiloss": run_multiloss,
        "distribution": run_distribution,
        "optional": run_optional,
    }

    checks: list[dict[str, Any]] = []
    for case in cases_to_run(args.case):
        checks.extend(runners[case](rt, args, device))

    print(
        json.dumps(
            {
                "status": "ok",
                "device": device,
                "batch_size": args.batch_size,
                "horizon": args.horizon,
                "quantiles": list(args.quantiles),
                "checks": checks,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"check_metrics_shapes.py failed: {exc}", file=sys.stderr)
        raise
