import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "frechet_distance.py"
spec = importlib.util.spec_from_file_location("frechet_distance", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

same = mod.calculate_frechet_distance([0, 0], [[1, 0], [0, 1]], [0, 0], [[1, 0], [0, 1]])
assert abs(same["fid"]) < 1e-8
shift = mod.calculate_frechet_distance([0, 0], [[1, 0], [0, 1]], [1, 0], [[1, 0], [0, 1]])
assert shift["fid"] > same["fid"]
bigger = mod.calculate_frechet_distance([0, 0], [[1, 0], [0, 1]], [2, 0], [[1, 0], [0, 1]])
assert bigger["fid"] > shift["fid"]
