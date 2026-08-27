#!/usr/bin/env python3
"""Tiny synthetic smoke tests for PyTorch Geometric Temporal recurrent layers.

The script intentionally avoids dataset downloads, plotting, Lightning, GPUs, and
long training. It checks that selected recurrent layers can import, run a CPU
forward pass, attach an explicit nonlinearity + Linear head, compute a tiny MSE
loss, and take one or more optimizer steps.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Tuple

import torch
import torch.nn.functional as F

from torch_geometric_temporal.nn.recurrent import (
    A3TGCN,
    A3TGCN2,
    AGCRN,
    BatchedDCRNN,
    DCRNN,
    DyGrEncoder,
    EvolveGCNH,
    EvolveGCNO,
    GCLSTM,
    GConvGRU,
    GConvLSTM,
    LRGCN,
    MPNNLSTM,
    TGCN,
    TGCN2,
)

LAYER_CHOICES = [
    "all",
    "gconvgru",
    "gconvlstm",
    "gclstm",
    "lrgcn",
    "dygrencoder",
    "evolvegcnh",
    "evolvegcno",
    "dcrnn",
    "batcheddcrnn",
    "tgcn",
    "tgcn2",
    "a3tgcn",
    "a3tgcn2",
    "mpnnlstm",
    "agcrn",
]


@dataclass
class SmokeResult:
    layer: str
    output_shape: Tuple[int, ...]
    target_shape: Tuple[int, ...]
    final_loss: float


def set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)


def ring_graph(num_nodes: int) -> Tuple[torch.Tensor, torch.Tensor]:
    """Create a deterministic bidirectional ring with positive weights."""
    if num_nodes < 3:
        raise ValueError("num_nodes must be at least 3 for the synthetic ring graph")
    edges: List[Tuple[int, int]] = []
    for node in range(num_nodes):
        nxt = (node + 1) % num_nodes
        edges.append((node, nxt))
        edges.append((nxt, node))
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    edge_weight = torch.ones(edge_index.size(1), dtype=torch.float32)
    return edge_index, edge_weight


def synthetic_snapshots(steps: int, num_nodes: int, in_channels: int) -> List[torch.Tensor]:
    base = torch.linspace(-1.0, 1.0, steps=num_nodes * in_channels, dtype=torch.float32)
    base = base.view(num_nodes, in_channels)
    snapshots = []
    for step in range(steps):
        snapshots.append(torch.sin(base + float(step) / max(1, steps)))
    return snapshots


def target_from_hidden_shape(shape: Iterable[int]) -> torch.Tensor:
    return torch.zeros(tuple(shape), dtype=torch.float32)


class OneStateForecaster(torch.nn.Module):
    def __init__(self, layer: torch.nn.Module, hidden_dim: int, target_dim: int = 1):
        super().__init__()
        self.layer = layer
        self.head = torch.nn.Linear(hidden_dim, target_dim)

    def forward(self, x, edge_index, edge_weight, h=None):
        h = self.layer(x, edge_index, edge_weight, h)
        return self.head(F.relu(h)), h


class TwoStateForecaster(torch.nn.Module):
    def __init__(self, layer: torch.nn.Module, hidden_dim: int, target_dim: int = 1):
        super().__init__()
        self.layer = layer
        self.head = torch.nn.Linear(hidden_dim, target_dim)

    def forward(self, x, edge_index, edge_weight, h=None, c=None, lambda_max=None):
        h, c = self.layer(x, edge_index, edge_weight, h, c, lambda_max)
        return self.head(F.relu(h)), h, c


class LRGCNForecaster(torch.nn.Module):
    def __init__(self, in_channels: int, hidden_dim: int, num_relations: int):
        super().__init__()
        self.layer = LRGCN(in_channels, hidden_dim, num_relations=num_relations, num_bases=2)
        self.head = torch.nn.Linear(hidden_dim, 1)

    def forward(self, x, edge_index, edge_type, h=None, c=None):
        h, c = self.layer(x, edge_index, edge_type, h, c)
        return self.head(F.relu(h)), h, c


class DyGrEncoderForecaster(torch.nn.Module):
    def __init__(self, conv_out_channels: int, lstm_out_channels: int):
        super().__init__()
        self.layer = DyGrEncoder(
            conv_out_channels=conv_out_channels,
            conv_num_layers=2,
            conv_aggr="add",
            lstm_out_channels=lstm_out_channels,
            lstm_num_layers=1,
        )
        self.head = torch.nn.Linear(lstm_out_channels, 1)

    def forward(self, x, edge_index, edge_weight, h=None, c=None):
        h_tilde, h, c = self.layer(x, edge_index, edge_weight, h, c)
        return self.head(F.relu(h_tilde)), h, c


class EvolveForecaster(torch.nn.Module):
    def __init__(self, layer: torch.nn.Module, hidden_dim: int):
        super().__init__()
        self.layer = layer
        self.head = torch.nn.Linear(hidden_dim, 1)

    def reset_sequence(self) -> None:
        if hasattr(self.layer, "reinitialize_weight"):
            self.layer.reinitialize_weight()

    def forward(self, x, edge_index, edge_weight):
        x = self.layer(x, edge_index, edge_weight)
        return self.head(F.relu(x))


class A3Forecaster(torch.nn.Module):
    def __init__(self, in_channels: int, hidden_dim: int, periods: int):
        super().__init__()
        self.periods = periods
        self.layer = A3TGCN(in_channels, hidden_dim, periods=periods)
        self.head = torch.nn.Linear(hidden_dim, 1)

    def forward(self, x_periods, edge_index, edge_weight, h=None):
        h = self.layer(x_periods, edge_index, edge_weight, h)
        return self.head(F.relu(h)), h


class TGCN2SequenceForecaster(torch.nn.Module):
    def __init__(self, in_channels: int, hidden_dim: int, batch_size: int):
        super().__init__()
        self.layer = TGCN2(in_channels, hidden_dim, batch_size=batch_size)
        self.head = torch.nn.Linear(hidden_dim, 1)

    def forward(self, x_periods, edge_index, edge_weight, h=None):
        # x_periods: [B, N, F, T]
        outputs = []
        for period in range(x_periods.size(-1)):
            h = self.layer(x_periods[..., period], edge_index, edge_weight, h)
            outputs.append(self.head(F.relu(h)).unsqueeze(1))
        return torch.cat(outputs, dim=1), h


class A3BatchedForecaster(torch.nn.Module):
    def __init__(self, in_channels: int, hidden_dim: int, periods: int, batch_size: int):
        super().__init__()
        self.periods = periods
        self.layer = A3TGCN2(in_channels, hidden_dim, periods=periods, batch_size=batch_size)
        self.head = torch.nn.Linear(hidden_dim, periods)

    def forward(self, x_periods, edge_index, edge_weight, h=None):
        h = self.layer(x_periods, edge_index, edge_weight, h)
        return self.head(F.relu(h)), h


class BatchedDCRNNForecaster(torch.nn.Module):
    def __init__(self, in_channels: int, hidden_dim: int):
        super().__init__()
        self.layer = BatchedDCRNN(in_channels, hidden_dim, K=2)
        self.head = torch.nn.Linear(hidden_dim, 1)

    def forward(self, x_seq, edge_index, edge_weight):
        h_seq = self.layer(x_seq, edge_index, edge_weight)
        return self.head(F.relu(h_seq))


class MPNNLSTMForecaster(torch.nn.Module):
    def __init__(self, in_channels: int, hidden_size: int, num_nodes: int, window: int):
        super().__init__()
        self.layer = MPNNLSTM(in_channels, hidden_size, num_nodes=num_nodes, window=window, dropout=0.0)
        self.head = torch.nn.Linear(2 * hidden_size + in_channels + window - 1, 1)

    def forward(self, x, edge_index, edge_weight):
        h = self.layer(x, edge_index, edge_weight)
        return self.head(F.relu(h))


class AGCRNForecaster(torch.nn.Module):
    def __init__(self, num_nodes: int, in_channels: int, hidden_dim: int, emb_dim: int):
        super().__init__()
        self.emb = torch.nn.Parameter(torch.empty(num_nodes, emb_dim))
        torch.nn.init.xavier_uniform_(self.emb)
        self.layer = AGCRN(num_nodes, in_channels, hidden_dim, K=2, embedding_dimensions=emb_dim)
        self.head = torch.nn.Linear(hidden_dim, 1)

    def forward(self, x, h=None):
        h = self.layer(x, self.emb, h)
        return self.head(F.relu(h)), h


def train_basic_one_state(args, layer_name: str, layer_factory: Callable[[], torch.nn.Module]) -> SmokeResult:
    edge_index, edge_weight = ring_graph(args.num_nodes)
    xs = synthetic_snapshots(args.steps, args.num_nodes, args.in_channels)
    model = OneStateForecaster(layer_factory(), args.hidden_channels)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    final_y_hat = None
    final_target = None
    final_loss = None
    for _ in range(args.train_steps):
        h = None
        loss = torch.tensor(0.0)
        optimizer.zero_grad()
        for x in xs:
            y_hat, h = model(x, edge_index, edge_weight, h)
            target = target_from_hidden_shape(y_hat.shape)
            loss = loss + F.mse_loss(y_hat, target)
            final_y_hat, final_target = y_hat, target
        loss = loss / len(xs)
        loss.backward()
        optimizer.step()
        final_loss = loss.detach()
    assert final_y_hat is not None and final_target is not None and final_loss is not None
    expected = (args.num_nodes, 1)
    assert tuple(final_y_hat.shape) == expected, (layer_name, tuple(final_y_hat.shape), expected)
    return SmokeResult(layer_name, tuple(final_y_hat.shape), tuple(final_target.shape), float(final_loss))


def train_basic_two_state(args, layer_name: str, layer_factory: Callable[[], torch.nn.Module]) -> SmokeResult:
    edge_index, edge_weight = ring_graph(args.num_nodes)
    xs = synthetic_snapshots(args.steps, args.num_nodes, args.in_channels)
    model = TwoStateForecaster(layer_factory(), args.hidden_channels)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    final_y_hat = None
    final_target = None
    final_loss = None
    for _ in range(args.train_steps):
        h, c = None, None
        loss = torch.tensor(0.0)
        optimizer.zero_grad()
        for x in xs:
            y_hat, h, c = model(x, edge_index, edge_weight, h, c)
            target = target_from_hidden_shape(y_hat.shape)
            loss = loss + F.mse_loss(y_hat, target)
            final_y_hat, final_target = y_hat, target
        loss = loss / len(xs)
        loss.backward()
        optimizer.step()
        final_loss = loss.detach()
    assert final_y_hat is not None and final_target is not None and final_loss is not None
    expected = (args.num_nodes, 1)
    assert tuple(final_y_hat.shape) == expected, (layer_name, tuple(final_y_hat.shape), expected)
    return SmokeResult(layer_name, tuple(final_y_hat.shape), tuple(final_target.shape), float(final_loss))


def train_lrgcn(args) -> SmokeResult:
    edge_index, _ = ring_graph(args.num_nodes)
    edge_type = torch.arange(edge_index.size(1), dtype=torch.long) % 3
    xs = synthetic_snapshots(args.steps, args.num_nodes, args.in_channels)
    model = LRGCNForecaster(args.in_channels, args.hidden_channels, num_relations=3)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    final_y_hat = final_target = final_loss = None
    for _ in range(args.train_steps):
        h, c = None, None
        loss = torch.tensor(0.0)
        optimizer.zero_grad()
        for x in xs:
            y_hat, h, c = model(x, edge_index, edge_type, h, c)
            target = target_from_hidden_shape(y_hat.shape)
            loss = loss + F.mse_loss(y_hat, target)
            final_y_hat, final_target = y_hat, target
        loss = loss / len(xs)
        loss.backward()
        optimizer.step()
        final_loss = loss.detach()
    expected = (args.num_nodes, 1)
    assert tuple(final_y_hat.shape) == expected
    return SmokeResult("lrgcn", tuple(final_y_hat.shape), tuple(final_target.shape), float(final_loss))


def train_dygrencoder(args) -> SmokeResult:
    edge_index, edge_weight = ring_graph(args.num_nodes)
    xs = synthetic_snapshots(args.steps, args.num_nodes, args.in_channels)
    conv_out = max(args.hidden_channels, args.in_channels)
    model = DyGrEncoderForecaster(conv_out_channels=conv_out, lstm_out_channels=args.hidden_channels)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    final_y_hat = final_target = final_loss = None
    for _ in range(args.train_steps):
        h, c = None, None
        loss = torch.tensor(0.0)
        optimizer.zero_grad()
        for x in xs:
            y_hat, h, c = model(x, edge_index, edge_weight, h, c)
            target = target_from_hidden_shape(y_hat.shape)
            loss = loss + F.mse_loss(y_hat, target)
            final_y_hat, final_target = y_hat, target
        loss = loss / len(xs)
        loss.backward()
        optimizer.step()
        final_loss = loss.detach()
    expected = (args.num_nodes, 1)
    assert tuple(final_y_hat.shape) == expected
    return SmokeResult("dygrencoder", tuple(final_y_hat.shape), tuple(final_target.shape), float(final_loss))


def train_evolve(args, layer_name: str, layer_factory: Callable[[], torch.nn.Module]) -> SmokeResult:
    if args.in_channels > args.num_nodes and layer_name == "evolvegcnh":
        raise ValueError("For this EvolveGCNH smoke, set --in-channels <= --num-nodes")
    edge_index, edge_weight = ring_graph(args.num_nodes)
    xs = synthetic_snapshots(args.steps, args.num_nodes, args.in_channels)
    model = EvolveForecaster(layer_factory(), hidden_dim=args.in_channels)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    final_y_hat = final_target = final_loss = None
    for _ in range(args.train_steps):
        model.reset_sequence()
        loss = torch.tensor(0.0)
        optimizer.zero_grad()
        for x in xs:
            y_hat = model(x, edge_index, edge_weight)
            target = target_from_hidden_shape(y_hat.shape)
            loss = loss + F.mse_loss(y_hat, target)
            final_y_hat, final_target = y_hat, target
        loss = loss / len(xs)
        loss.backward()
        optimizer.step()
        final_loss = loss.detach()
    expected = (args.num_nodes, 1)
    assert tuple(final_y_hat.shape) == expected
    return SmokeResult(layer_name, tuple(final_y_hat.shape), tuple(final_target.shape), float(final_loss))


def train_a3tgcn(args) -> SmokeResult:
    edge_index, edge_weight = ring_graph(args.num_nodes)
    model = A3Forecaster(args.in_channels, args.hidden_channels, periods=args.periods)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    final_y_hat = final_target = final_loss = None
    for _ in range(args.train_steps):
        h = None
        loss = torch.tensor(0.0)
        optimizer.zero_grad()
        for step in range(args.steps):
            x = torch.randn(args.num_nodes, args.in_channels, args.periods) * 0.1 + step / 10.0
            y_hat, h = model(x, edge_index, edge_weight, h)
            target = target_from_hidden_shape(y_hat.shape)
            loss = loss + F.mse_loss(y_hat, target)
            final_y_hat, final_target = y_hat, target
        loss = loss / args.steps
        loss.backward()
        optimizer.step()
        final_loss = loss.detach()
    expected = (args.num_nodes, 1)
    assert tuple(final_y_hat.shape) == expected
    return SmokeResult("a3tgcn", tuple(final_y_hat.shape), tuple(final_target.shape), float(final_loss))


def train_tgcn2(args) -> SmokeResult:
    edge_index, edge_weight = ring_graph(args.num_nodes)
    model = TGCN2SequenceForecaster(args.in_channels, args.hidden_channels, batch_size=args.batch_size)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    final_y_hat = final_target = final_loss = None
    for _ in range(args.train_steps):
        h = None
        optimizer.zero_grad()
        x = torch.randn(args.batch_size, args.num_nodes, args.in_channels, args.periods)
        y_hat, h = model(x, edge_index, edge_weight, h)
        target = target_from_hidden_shape(y_hat.shape)
        loss = F.mse_loss(y_hat, target)
        loss.backward()
        optimizer.step()
        final_y_hat, final_target, final_loss = y_hat, target, loss.detach()
    expected = (args.batch_size, args.periods, args.num_nodes, 1)
    assert tuple(final_y_hat.shape) == expected, (tuple(final_y_hat.shape), expected)
    return SmokeResult("tgcn2", tuple(final_y_hat.shape), tuple(final_target.shape), float(final_loss))


def train_a3tgcn2(args) -> SmokeResult:
    edge_index, edge_weight = ring_graph(args.num_nodes)
    model = A3BatchedForecaster(args.in_channels, args.hidden_channels, periods=args.periods, batch_size=args.batch_size)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    final_y_hat = final_target = final_loss = None
    for _ in range(args.train_steps):
        h = None
        optimizer.zero_grad()
        x = torch.randn(args.batch_size, args.num_nodes, args.in_channels, args.periods)
        y_hat, h = model(x, edge_index, edge_weight, h)
        target = target_from_hidden_shape(y_hat.shape)
        loss = F.mse_loss(y_hat, target)
        loss.backward()
        optimizer.step()
        final_y_hat, final_target, final_loss = y_hat, target, loss.detach()
    expected = (args.batch_size, args.num_nodes, args.periods)
    assert tuple(final_y_hat.shape) == expected, (tuple(final_y_hat.shape), expected)
    return SmokeResult("a3tgcn2", tuple(final_y_hat.shape), tuple(final_target.shape), float(final_loss))


def train_batcheddcrnn(args) -> SmokeResult:
    edge_index, edge_weight = ring_graph(args.num_nodes)
    model = BatchedDCRNNForecaster(args.in_channels, args.hidden_channels)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    final_y_hat = final_target = final_loss = None
    for _ in range(args.train_steps):
        optimizer.zero_grad()
        x = torch.randn(args.batch_size, args.steps, args.num_nodes, args.in_channels)
        y_hat = model(x, edge_index, edge_weight)
        target = target_from_hidden_shape(y_hat.shape)
        loss = F.mse_loss(y_hat, target)
        loss.backward()
        optimizer.step()
        final_y_hat, final_target, final_loss = y_hat, target, loss.detach()
    expected = (args.batch_size, args.steps, args.num_nodes, 1)
    assert tuple(final_y_hat.shape) == expected, (tuple(final_y_hat.shape), expected)
    return SmokeResult("batcheddcrnn", tuple(final_y_hat.shape), tuple(final_target.shape), float(final_loss))


def train_mpnnlstm(args) -> SmokeResult:
    edge_index, edge_weight = ring_graph(args.num_nodes)
    model = MPNNLSTMForecaster(args.in_channels, args.hidden_channels, args.num_nodes, window=1)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    final_y_hat = final_target = final_loss = None
    for _ in range(args.train_steps):
        optimizer.zero_grad()
        x = torch.randn(args.num_nodes, args.in_channels)
        y_hat = model(x, edge_index, edge_weight)
        target = target_from_hidden_shape(y_hat.shape)
        loss = F.mse_loss(y_hat, target)
        loss.backward()
        optimizer.step()
        final_y_hat, final_target, final_loss = y_hat, target, loss.detach()
    expected = (args.num_nodes, 1)
    assert tuple(final_y_hat.shape) == expected, (tuple(final_y_hat.shape), expected)
    return SmokeResult("mpnnlstm", tuple(final_y_hat.shape), tuple(final_target.shape), float(final_loss))


def train_agcrn(args) -> SmokeResult:
    model = AGCRNForecaster(args.num_nodes, args.in_channels, args.hidden_channels, emb_dim=max(2, args.in_channels))
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    final_y_hat = final_target = final_loss = None
    for _ in range(args.train_steps):
        h = None
        loss = torch.tensor(0.0)
        optimizer.zero_grad()
        for _step in range(args.steps):
            x = torch.randn(args.batch_size, args.num_nodes, args.in_channels)
            y_hat, h = model(x, h)
            target = target_from_hidden_shape(y_hat.shape)
            loss = loss + F.mse_loss(y_hat, target)
            final_y_hat, final_target = y_hat, target
        loss = loss / args.steps
        loss.backward()
        optimizer.step()
        final_loss = loss.detach()
    expected = (args.batch_size, args.num_nodes, 1)
    assert tuple(final_y_hat.shape) == expected, (tuple(final_y_hat.shape), expected)
    return SmokeResult("agcrn", tuple(final_y_hat.shape), tuple(final_target.shape), float(final_loss))


def registry(args) -> Dict[str, Callable[[], SmokeResult]]:
    return {
        "gconvgru": lambda: train_basic_one_state(
            args, "gconvgru", lambda: GConvGRU(args.in_channels, args.hidden_channels, K=2)
        ),
        "gconvlstm": lambda: train_basic_two_state(
            args, "gconvlstm", lambda: GConvLSTM(args.in_channels, args.hidden_channels, K=2)
        ),
        "gclstm": lambda: train_basic_two_state(
            args, "gclstm", lambda: GCLSTM(args.in_channels, args.hidden_channels, K=2)
        ),
        "lrgcn": lambda: train_lrgcn(args),
        "dygrencoder": lambda: train_dygrencoder(args),
        "evolvegcnh": lambda: train_evolve(
            args, "evolvegcnh", lambda: EvolveGCNH(num_of_nodes=args.num_nodes, in_channels=args.in_channels)
        ),
        "evolvegcno": lambda: train_evolve(
            args, "evolvegcno", lambda: EvolveGCNO(in_channels=args.in_channels)
        ),
        "dcrnn": lambda: train_basic_one_state(
            args, "dcrnn", lambda: DCRNN(args.in_channels, args.hidden_channels, K=2)
        ),
        "batcheddcrnn": lambda: train_batcheddcrnn(args),
        "tgcn": lambda: train_basic_one_state(
            args, "tgcn", lambda: TGCN(args.in_channels, args.hidden_channels)
        ),
        "tgcn2": lambda: train_tgcn2(args),
        "a3tgcn": lambda: train_a3tgcn(args),
        "a3tgcn2": lambda: train_a3tgcn2(args),
        "mpnnlstm": lambda: train_mpnnlstm(args),
        "agcrn": lambda: train_agcrn(args),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic, no-download CPU smoke for PyTorch Geometric "
            "Temporal recurrent layers with explicit ReLU + Linear heads."
        )
    )
    parser.add_argument("--layer", choices=LAYER_CHOICES, default="gconvgru", help="Layer smoke to run.")
    parser.add_argument("--num-nodes", type=int, default=5, help="Synthetic graph node count; use at least 3.")
    parser.add_argument("--in-channels", type=int, default=3, help="Input feature channels.")
    parser.add_argument("--hidden-channels", type=int, default=4, help="Hidden/output channels for recurrent layers.")
    parser.add_argument("--steps", type=int, default=3, help="Synthetic temporal steps or sequence length.")
    parser.add_argument("--periods", type=int, default=3, help="Period dimension for A3/TGCN2-style batched examples.")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size for batch-aware recurrent examples.")
    parser.add_argument("--train-steps", type=int, default=1, help="Tiny optimizer steps to run.")
    parser.add_argument("--lr", type=float, default=0.01, help="Learning rate for the tiny optimizer.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for reproducible tensors.")
    parser.add_argument("--json", action="store_true", help="Print JSON summary only.")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if args.num_nodes < 3:
        raise SystemExit("--num-nodes must be at least 3")
    if args.in_channels < 1 or args.hidden_channels < 1:
        raise SystemExit("--in-channels and --hidden-channels must be positive")
    if args.steps < 1 or args.periods < 1 or args.batch_size < 1 or args.train_steps < 1:
        raise SystemExit("--steps, --periods, --batch-size, and --train-steps must be positive")
    if not math.isfinite(args.lr) or args.lr <= 0:
        raise SystemExit("--lr must be a positive finite value")


def main() -> None:
    args = parse_args()
    validate_args(args)
    set_seed(args.seed)
    torch.set_num_threads(1)

    runs = registry(args)
    selected = [name for name in runs if args.layer == "all" or args.layer == name]
    results = [runs[name]() for name in selected]

    payload = {
        "device": "cpu",
        "seed": args.seed,
        "results": [
            {
                "layer": r.layer,
                "output_shape": list(r.output_shape),
                "target_shape": list(r.target_shape),
                "final_loss": r.final_loss,
            }
            for r in results
        ],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("recurrent_forecasting_smoke: ok")
        for result in results:
            print(
                f"- {result.layer}: output={result.output_shape} "
                f"target={result.target_shape} loss={result.final_loss:.6f}"
            )


if __name__ == "__main__":
    main()
