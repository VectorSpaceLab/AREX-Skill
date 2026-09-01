import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "sampler.py"
spec = importlib.util.spec_from_file_location("sampler", script)
sampler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sampler)


def test_reproducible_interior_and_boundary():
    first = sampler.sample_hypercube(3, 5, seed=7)
    second = sampler.sample_hypercube(3, 5, seed=7)
    assert first == second
    boundary, faces = sampler.sample_boundary(3, 12, seed=8)
    assert len(boundary) == len(faces) == 12
    for point, face in zip(boundary, faces):
        assert all(0.0 <= value <= 1.0 for value in point)
        assert point[face["axis"]] == face["side"]
        assert face["side"] in (0.0, 1.0)
    coverage = sampler.face_coverage(faces, 3)
    assert coverage["all_faces"]


if __name__ == "__main__":
    test_reproducible_interior_and_boundary()
