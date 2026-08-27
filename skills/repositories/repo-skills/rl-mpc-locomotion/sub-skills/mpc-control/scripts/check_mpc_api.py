#!/usr/bin/env python3
"""Read-only CPU-side API and compiled-extension smoke check.

This intentionally does not import Isaac Gym, construct a simulator, open a viewer,
load a checkpoint, or execute a long control loop.
"""

from __future__ import print_function

import argparse
import sys


def check(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiet", action="store_true", help="print only failures or the final status"
    )
    args = parser.parse_args()
    checks = []

    try:
        import mpc_osqp

        required = ("ConvexMpc", "QPSolverName", "OSQP", "QPOASES", "TEST")
        for name in required:
            check(hasattr(mpc_osqp, name), "mpc_osqp is missing {!r}".format(name))
        check(int(mpc_osqp.TEST) == 42, "unexpected mpc_osqp.TEST value")
        solver = mpc_osqp.ConvexMpc(
            10.0,
            [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0],
            4,
            10,
            0.01,
            1e-5,
            mpc_osqp.QPOASES,
        )
        solver.reset_solver()
        checks.append("compiled extension symbols and constructor")
    except Exception as exc:
        print("FAIL: mpc_osqp: {}: {}".format(type(exc).__name__, exc))
        return 2

    try:
        import numpy as np
        from MPC_Controller.common.DesiredStateCommand import DesiredStateCommand
        from MPC_Controller.common.FootSwingTrajectory import FootSwingTrajectory
        from MPC_Controller.common.Quadruped import Quadruped, RobotType
        from MPC_Controller.convex_MPC.Gait import OffsetDurationGait
        from MPC_Controller.utils import ControllerType, FSM_StateName, GaitType

        check(
            tuple(name for name in ("ALIENGO", "A1", "GO1") if hasattr(RobotType, name))
            == ("ALIENGO", "A1", "GO1"),
            "public RobotType set is incomplete",
        )
        check(
            tuple(name for name in ("FSM", "MIN", "POLICY") if hasattr(ControllerType, name))
            == ("FSM", "MIN", "POLICY"),
            "public ControllerType set is incomplete",
        )
        check(
            tuple(name for name in ("TROT", "WALK", "BOUND") if hasattr(GaitType, name))
            == ("TROT", "WALK", "BOUND"),
            "public GaitType set is incomplete",
        )
        check(hasattr(FSM_StateName, "RECOVERY_STAND"), "FSM recovery state is missing")

        for robot_type in RobotType:
            quad = Quadruped(robot_type)
            check(quad.getHipLocation(0).shape == (3, 1), "hip shape is not (3, 1)")
            check(quad._friction_coeffs.shape == (4,), "friction shape is not (4,)")
            check(quad._mpc_weights.shape == (13,), "default weight shape is not (13,)")

        command = DesiredStateCommand()
        command.updateCommand([0.0, 0.0, 0.0] + [1.0] * 13)
        check(len(command.mpc_weights) == 13, "direct command weights are not length 13")
        command.reset()
        command.updateCommand([0.0, 0.0, 0.0], [1.0] * 12)
        check(len(command.mpc_weights) == 13, "policy command weights are not length 13")

        gait = OffsetDurationGait(
            10,
            np.array([0, 5, 5, 0], dtype=np.float32),
            np.array([5, 5, 5, 5], dtype=np.float32),
            "probe",
        )
        gait.setIterations(3, 0)
        check(gait.getContactState().shape == (4, 1), "contact phase shape is not (4, 1)")
        check(gait.getSwingState().shape == (4, 1), "swing phase shape is not (4, 1)")
        check(len(gait.getMpcTable()) == 40, "MPC table is not horizon*legs")

        swing = FootSwingTrajectory()
        initial = np.zeros((3, 1), dtype=np.float32)
        final = np.array([[0.1], [0.0], [-0.1]], dtype=np.float32)
        swing.setInitialPosition(initial)
        swing.setFinalPosition(final)
        swing.setHeight(0.05)
        swing.computeSwingTrajectoryBezier(0.5, 0.1)
        check(swing.getPosition().shape == (3, 1), "swing position shape is not (3, 1)")
        checks.append("enums, robot geometry, command, gait, and swing contracts")
    except Exception as exc:
        print("FAIL: Python MPC API: {}: {}".format(type(exc).__name__, exc))
        return 3

    if not args.quiet:
        for item in checks:
            print("PASS: {}".format(item))
    print("PASS: mpc-control CPU API smoke")
    return 0


if __name__ == "__main__":
    sys.exit(main())
