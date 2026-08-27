#!/usr/bin/env python3
"""CLI and config smoke for DI-engine.

This script checks that the installed package still exposes the public CLI
entry points and can compile a representative CartPole config.
"""

from __future__ import annotations

from click.testing import CliRunner

from ding.entry.cli import cli
from ding.entry.cli_ditask import cli_ditask
from ding.config import compile_config
from dizoo.classic_control.cartpole.config.cartpole_dqn_config import (
    cartpole_dqn_config,
    cartpole_dqn_create_config,
)


def main() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0, result.output

    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0, result.output

    result = runner.invoke(cli_ditask, ["--help"])
    assert result.exit_code == 0, result.output

    cfg = compile_config(
        cartpole_dqn_config,
        create_cfg=cartpole_dqn_create_config,
        auto=True,
        save_cfg=False,
    )
    print(f"compiled: {cfg.exp_name} / stop_value={cfg.env.stop_value} / cuda={cfg.policy.cuda}")
    print("cli smoke ok")


if __name__ == '__main__':
    main()
