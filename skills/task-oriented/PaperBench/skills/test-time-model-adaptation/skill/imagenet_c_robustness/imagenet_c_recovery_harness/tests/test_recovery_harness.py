import importlib.util
import json
import pathlib
import tempfile

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "run_recovery.py"
spec = importlib.util.spec_from_file_location("run_recovery", SCRIPT)
run_recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_recovery)


def test_dataset_generation_and_error_rate():
    samples = run_recovery.build_dataset(4, 4)
    assert len(samples) == 4
    assert [item["label"] for item in samples] == [0, 1, 0, 1]
    error = run_recovery.error_rate(samples, run_recovery.evaluated_classifier)
    assert 0.0 <= error <= 1.0


def test_write_json_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = pathlib.Path(tmpdir) / "nested" / "payload.json"
        run_recovery.write_json(path, {"ok": True})
        assert json.loads(path.read_text(encoding="utf-8"))["ok"] is True


if __name__ == "__main__":
    test_dataset_generation_and_error_rate()
    test_write_json_roundtrip()
