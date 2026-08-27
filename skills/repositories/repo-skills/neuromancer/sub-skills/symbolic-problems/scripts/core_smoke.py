#!/usr/bin/env python3
"""Run a deterministic, CPU-only NeuroMANCER symbolic Problem smoke check.

This helper intentionally avoids MLPs, data loaders, network access, training
loops, plotting, and file writes. It is safe to invoke from any working
 directory after the ``neuromancer`` distribution is installed.
"""

import argparse


def run_smoke() -> None:
    """Construct a tiny Node, symbolic objective/constraint, and Problem."""
    import torch
    from neuromancer.constraint import variable
    from neuromancer.loss import PenaltyLoss
    from neuromancer.problem import Problem
    from neuromancer.system import Node

    torch.manual_seed(0)
    linear = torch.nn.Linear(1, 1)
    mapper = Node(linear, ["p"], ["x"], name="linear_map")

    p = variable("p")
    x = variable("x")
    objective = ((x - p) ** 2).minimize(
        metric=torch.mean, weight=1.0, name="fit"
    )
    bound = x >= -2.0
    bound.update_name("lower_bound")

    loss = PenaltyLoss([objective], [bound])
    problem = Problem([mapper], loss, check_overwrite=True)
    batch = {
        "p": torch.tensor([[0.25], [0.50]], dtype=torch.float32),
        "name": "smoke",
    }

    output = problem(batch)
    total = output["smoke_loss"]
    assert total.ndim == 0, f"expected scalar loss, got {tuple(total.shape)}"
    assert total.requires_grad, "symbolic Problem loss is detached"
    assert "smoke_objective_loss" in output
    assert "smoke_penalty_loss" in output
    assert "smoke_lower_bound" in output

    total.backward()
    assert linear.weight.grad is not None, "Node parameter received no gradient"
    assert torch.isfinite(total).item(), "loss is not finite"
    print("core_smoke: PASS (CPU symbolic Node/Problem autograd check)")


def main() -> None:
    """Parse the CLI and optionally run the smoke."""
    parser = argparse.ArgumentParser(
        description="Run a deterministic CPU-only NeuroMANCER symbolic smoke."
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="construct the tiny Node/Problem and run assertions",
    )
    args = parser.parse_args()
    if args.run:
        run_smoke()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
