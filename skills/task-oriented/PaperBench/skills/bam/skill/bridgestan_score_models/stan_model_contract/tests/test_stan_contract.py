import importlib.util
from pathlib import Path
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "stan_contract.py"
spec = importlib.util.spec_from_file_location("stan_contract", SCRIPT); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def test_bernoulli_contract():
    source = """data { int<lower=0> N; array[N] int<lower=0, upper=1> y; }
parameters { real<lower=0,upper=1> theta; }
transformed parameters { real logit_theta = logit(theta); }
model { theta ~ beta(1, 1); y ~ bernoulli(theta); }
generated quantities { int y_sim = bernoulli_rng(theta); }
"""
    contract = mod.parse_stan_contract(source)
    assert not contract["diagnostics"]
    assert any(item["name"] == "N" for item in contract["data"])
    assert any(item["name"] == "y" and item["kind"] == "array" for item in contract["data"])
    theta = contract["parameters"][0]
    assert theta["name"] == "theta" and theta["lower"] == 0.0 and theta["upper"] == 1.0
    assert contract["transformed_parameters"][0]["expression"] == "logit(theta)"
    assert {term["distribution"] for term in contract["model_terms"]} == {"beta", "bernoulli"}
    assert contract["generated_quantities"][0]["name"] == "y_sim"
if __name__ == "__main__": test_bernoulli_contract()
