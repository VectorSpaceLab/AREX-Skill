import importlib.util
import pathlib

script_path = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "run_lpips_recovery.py"
spec = importlib.util.spec_from_file_location("run_lpips_recovery", script_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_make_triplets_has_valid_labels():
    triplets = module.make_triplets()
    assert len(triplets) == 6
    assert all(item["judge"] in (0, 1) for item in triplets)
    assert all("ref" in item and "p0" in item and "p1" in item for item in triplets)
