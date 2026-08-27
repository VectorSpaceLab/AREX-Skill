"""Synthetic nested-container optimizer smoke.

Uses only in-memory quadratic fixtures; no network, downloads, or plotting.
"""

from autograd import grad
from autograd.misc.flatten import flatten, flatten_func
from autograd.misc.optimizers import adam, rmsprop, sgd
import autograd.numpy as np


def make_tree():
    return {
        "encoder": [
            np.array([2.0, -1.5]),
            {
                "bias": np.array([0.5]),
                "scale": (np.array([-2.0]),),
            },
        ],
        "decoder": (
            np.array([1.0, -3.0]),
        ),
    }


def tree_loss(params):
    return (
        np.sum(params["encoder"][0] ** 2)
        + np.sum(params["encoder"][1]["bias"] ** 2)
        + np.sum(params["encoder"][1]["scale"][0] ** 2)
        + np.sum(params["decoder"][0] ** 2)
    )


def tree_loss_with_iter(params, _i):
    return tree_loss(params)


def assert_same_structure(expected, actual):
    assert type(expected) is type(actual)
    if isinstance(expected, dict):
        keys = sorted(expected.keys())
        assert keys == sorted(actual.keys())
        for key in keys:
            assert_same_structure(expected[key], actual[key])
    elif isinstance(expected, list):
        assert len(expected) == len(actual)
        for exp_item, act_item in zip(expected, actual):
            assert_same_structure(exp_item, act_item)
    elif isinstance(expected, tuple):
        assert len(expected) == len(actual)
        for exp_item, act_item in zip(expected, actual):
            assert_same_structure(exp_item, act_item)
    else:
        assert getattr(expected, "shape", None) == getattr(actual, "shape", None)


def assert_tree_allclose(expected, actual):
    assert_same_structure(expected, actual)
    if isinstance(expected, dict):
        for key in sorted(expected.keys()):
            assert_tree_allclose(expected[key], actual[key])
    elif isinstance(expected, list):
        for exp_item, act_item in zip(expected, actual):
            assert_tree_allclose(exp_item, act_item)
    elif isinstance(expected, tuple):
        for exp_item, act_item in zip(expected, actual):
            assert_tree_allclose(exp_item, act_item)
    else:
        assert np.allclose(expected, actual)



def run_optimizer(name, optimizer, **kwargs):
    init = make_tree()
    initial_loss = tree_loss(init)
    gradient = grad(tree_loss_with_iter)
    seen_losses = []

    def callback(params, i, g):
        if i == 0:
            assert_same_structure(init, params)
            assert_same_structure(init, g)
        seen_losses.append(float(tree_loss(params)))

    result = optimizer(gradient, init, callback=callback, **kwargs)
    final_loss = tree_loss(result)
    print(f"{name}: {initial_loss:.6f} -> {final_loss:.6f}")
    assert seen_losses, f"{name} callback never fired"
    assert final_loss < initial_loss
    return result



def main():
    init = make_tree()

    flat_init, unflatten = flatten(init)
    roundtrip = unflatten(flat_init)
    assert_tree_allclose(init, roundtrip)

    flat_loss, flat_unflatten, flat_tree = flatten_func(tree_loss, init)
    assert_tree_allclose(init, flat_unflatten(flat_tree))
    assert np.allclose(flat_loss(flat_tree), np.array([tree_loss(init)]))

    print("roundtrip ok:", flat_init)
    run_optimizer("sgd", sgd, num_iters=40, step_size=0.05, mass=0.8)
    run_optimizer("rmsprop", rmsprop, num_iters=80, step_size=0.03)
    run_optimizer("adam", adam, num_iters=80, step_size=0.05)


if __name__ == "__main__":
    main()
