import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from objective_contract import build_objective, validate_objective


objective = build_objective("synthetic", "test", 0.3)
assert validate_objective(objective)
assert objective["threat_model"]["norm"] == "linf"
assert objective["mechanism_checks"]["natural_only_training"] is False

try:
    build_objective("synthetic", "test", 0.0)
    raise AssertionError("zero epsilon should fail")
except ValueError:
    pass
