#!/usr/bin/env python3
"""Run a deterministic, file-free IKPy Chain/FK/IK API smoke check.

Prerequisite: ``ikpy`` plus its base NumPy/SciPy/SymPy dependencies must be
installed. Example: ``python scripts/smoke_chain.py``. The helper intentionally
uses only in-memory links; it does not load URDF/MJCF files, plot, download, or
write review artifacts.
"""

from __future__ import annotations

import argparse

import numpy as np

from ikpy.chain import Chain
from ikpy.link import DHLink, OriginLink, URDFLink
from ikpy.utils import geometry


def make_planar_chain(joint_bounds=(-np.pi, np.pi)) -> Chain:
    """Create a two-unit planar chain with one active revolute link."""
    links = [
        OriginLink(),
        URDFLink(
            name="planar_joint",
            origin_translation=np.array([1.0, 0.0, 0.0]),
            origin_orientation=np.zeros(3),
            rotation=np.array([0.0, 0.0, 1.0]),
            bounds=joint_bounds,
            use_symbolic_matrix=False,
            joint_type="revolute",
        ),
        URDFLink(
            name="tool_tip",
            origin_translation=np.array([1.0, 0.0, 0.0]),
            origin_orientation=np.zeros(3),
            use_symbolic_matrix=False,
            joint_type="fixed",
        ),
    ]
    chain = Chain(
        links=links,
        active_links_mask=[False, True, False],
        name="chain-smoke",
    )
    assert len(chain.links) == 3
    assert not bool(chain.active_links_mask[-1])
    return chain


def run_smoke() -> None:
    """Assert representative public behavior and fail loudly on regressions."""
    chain = make_planar_chain()
    q_zero = np.zeros(len(chain.links))
    q_quarter = np.array([0.0, np.pi / 2, 0.0])

    fk_zero = np.asarray(chain.forward_kinematics(q_zero))
    assert fk_zero.shape == (4, 4)
    np.testing.assert_allclose(fk_zero[:3, 3], [2.0, 0.0, 0.0], atol=1e-12)

    fk_quarter = np.asarray(chain.forward_kinematics(q_quarter))
    np.testing.assert_allclose(fk_quarter[:3, 3], [1.0, 1.0, 0.0], atol=1e-12)
    frames = chain.forward_kinematics(q_quarter, full_kinematics=True)
    assert len(frames) == len(chain.links)
    assert all(np.asarray(frame).shape == (4, 4) for frame in frames)

    try:
        chain.forward_kinematics([0.0, 0.0])
    except ValueError:
        pass
    else:
        raise AssertionError("FK accepted a joint vector shorter than links")

    active = chain.active_from_full(q_quarter)
    assert active.shape == (1,)
    np.testing.assert_allclose(chain.active_to_full([0.25], q_zero), [0.0, 0.25, 0.0])

    position_target = np.array([1.0, 1.0, 0.0])
    position_solution = chain.inverse_kinematics(
        target_position=position_target,
        initial_position=q_zero,
    )
    assert position_solution.shape == (len(chain.links),)
    np.testing.assert_allclose(
        np.asarray(chain.forward_kinematics(position_solution))[:3, 3],
        position_target,
        atol=1e-6,
    )

    orientation_solution = chain.inverse_kinematics(
        target_position=position_target,
        target_orientation=[0.0, 1.0, 0.0],
        orientation_mode="X",
        initial_position=q_zero,
    )
    np.testing.assert_allclose(
        np.asarray(chain.forward_kinematics(orientation_solution))[:3, 0],
        [0.0, 1.0, 0.0],
        atol=1e-5,
    )

    orientation_only = chain.inverse_kinematics(
        target_orientation=np.eye(3),
        orientation_mode="all",
        initial_position=q_quarter,
    )
    np.testing.assert_allclose(
        np.asarray(chain.forward_kinematics(orientation_only))[:3, :3],
        np.eye(3),
        atol=1e-5,
    )

    bounded = make_planar_chain(joint_bounds=(-0.25, 0.25))
    bounded_solution = bounded.inverse_kinematics(
        target_position=[0.0, 2.0, 0.0],
        initial_position=q_zero,
    )
    assert -0.25 - 1e-12 <= bounded_solution[1] <= 0.25 + 1e-12

    prismatic = URDFLink(
        name="slide",
        origin_translation=np.zeros(3),
        origin_orientation=np.zeros(3),
        translation=np.array([1.0, 0.0, 0.0]),
        bounds=(0.0, 1.0),
        use_symbolic_matrix=False,
        joint_type="prismatic",
    )
    np.testing.assert_allclose(
        np.asarray(prismatic.get_link_frame_matrix(0.25))[:3, 3],
        [0.25, 0.0, 0.0],
        atol=1e-12,
    )

    dh = DHLink(
        name="dh_joint",
        d=0.0,
        a=1.0,
        alpha=0.0,
        theta=0.0,
        bounds=(-np.pi, np.pi),
        use_symbolic_matrix=False,
        length=1.0,
    )
    dh_frame = np.asarray(dh.get_link_frame_matrix(0.0))
    assert dh_frame.shape == (4, 4)
    np.testing.assert_allclose(dh_frame[:3, 3], [1.0, 0.0, 0.0], atol=1e-12)

    transform = geometry.to_transformation_matrix([1.0, 2.0, 3.0], np.eye(3))
    assert np.asarray(transform).shape == (4, 4)
    translation4, rotation = geometry.from_transformation_matrix(transform)
    assert np.asarray(translation4).shape == (4,)
    assert np.asarray(rotation).shape == (3, 3)
    np.testing.assert_allclose(translation4[:3], [1.0, 2.0, 3.0])


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a deterministic in-memory IKPy Chain/FK/IK smoke check."
    )
    parser.parse_args()
    run_smoke()
    print("chain-kinematics smoke: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
