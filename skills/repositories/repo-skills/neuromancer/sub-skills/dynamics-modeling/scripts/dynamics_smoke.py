#!/usr/bin/env python3
"""Run a bounded CPU smoke check for NeuroMANCER dynamics construction.

The check is deterministic, uses only tiny in-memory tensors, and performs no
training, downloads, file writes, or destructive operations. Use --help to
inspect the interface and --run to execute the package checks.
"""

import argparse
import sys


def run_smoke() -> int:
    """Build a tiny block, ODE model, and two one-step integrators."""
    try:
        import torch
        from neuromancer.modules.blocks import MLP
        from neuromancer.dynamics.ode import ODESystem, SSM
        from neuromancer.dynamics.integrators import Euler, RK4
    except ImportError as exc:
        print(
            "dynamics smoke unavailable: import failed. Install the target "
            "NeuroMANCER package and its declared ODE dependencies "
            "(torchdiffeq/torchsde), then rerun --run.\n"
            f"detail: {exc}",
            file=sys.stderr,
        )
        return 2

    torch.manual_seed(0)
    batch, nx, nu = 4, 2, 1

    block = MLP(
        nx + nu,
        nx,
        linear_map=torch.nn.Linear,
        nonlin=torch.nn.Tanh,
        hsizes=[4],
    )
    x = torch.zeros(batch, nx)
    u = torch.zeros(batch, nu)

    block_out = block(x, u)
    assert block_out.shape == (batch, nx), block_out.shape

    class TinyODE(ODESystem):
        """A deterministic autonomous RHS used only for this shape check."""

        def __init__(self):
            super().__init__(insize=nx, outsize=nx)
            self.rhs = MLP(
                nx,
                nx,
                linear_map=torch.nn.Linear,
                nonlin=torch.nn.Tanh,
                hsizes=[4],
            )

        def ode_equations(self, state):
            return self.rhs(state)

    ode = TinyODE()
    ode_out = ode(x)
    assert ode_out.shape == (batch, nx), ode_out.shape

    # Also verify the discrete state-space model contract without a rollout.
    fx = MLP(nx, nx, linear_map=torch.nn.Linear, nonlin=torch.nn.Tanh, hsizes=[4])
    fu = MLP(nu, nx, linear_map=torch.nn.Linear, nonlin=torch.nn.Tanh, hsizes=[4])
    ssm_out = SSM(fx, fu, nx=nx, nu=nu)(x, u)
    assert ssm_out.shape == (batch, nx), ssm_out.shape

    for integrator_type in (Euler, RK4):
        next_state = integrator_type(ode, h=0.01)(x)
        assert next_state.shape == (batch, nx), (
            integrator_type.__name__,
            next_state.shape,
        )

    print("PASS: block, SSM, ODE, Euler, and RK4 CPU shape checks")
    return 0


def main() -> int:
    """Parse arguments and optionally run the bounded smoke check."""
    parser = argparse.ArgumentParser(
        description="Run tiny deterministic NeuroMANCER dynamics shape checks."
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="run the CPU block, SSM, ODE, Euler, and RK4 checks",
    )
    args = parser.parse_args()
    if not args.run:
        parser.print_help()
        print("\nNo check run; pass --run to execute the smoke test.")
        return 0
    return run_smoke()


if __name__ == "__main__":
    raise SystemExit(main())
