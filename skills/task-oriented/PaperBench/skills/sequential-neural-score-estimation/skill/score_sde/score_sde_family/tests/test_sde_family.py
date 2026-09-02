import importlib.util
import pathlib

MODULE = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "sde_family.py"
spec = importlib.util.spec_from_file_location("sde_family", MODULE)
sde_family = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sde_family)


def test_sde_marginals_and_reverse_contracts():
    for kind in ["ve", "vp", "subvp"]:
        sde = sde_family.make_sde(kind, num_steps=10)
        drift, diffusion = sde.sde([1.0, -1.0], 0.5)
        mean, std = sde.marginal_prob([1.0, -1.0], 0.5)
        stochastic_drift, stochastic_diffusion = sde.reverse_drift_diffusion([1.0, -1.0], 0.5, [-0.1, 0.1])
        ode_drift, ode_diffusion = sde.reverse_drift_diffusion([1.0, -1.0], 0.5, [-0.1, 0.1], probability_flow=True)
        assert len(drift) == 2
        assert len(mean) == 2
        assert std > 0
        assert diffusion >= 0
        assert len(stochastic_drift) == 2
        assert stochastic_diffusion >= 0
        assert len(ode_drift) == 2
        assert ode_diffusion == 0.0
        assert sde.prior_logp([0.0, 1.0]) < 0
