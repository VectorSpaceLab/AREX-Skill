import json
import os
import subprocess
import sys
import tempfile


def test_cli_writes_importance_json():
    data = {
        "W0": [[1.0, 2.0]],
        "B": [[0.5]],
        "A": [[2.0, -1.0]],
        "grad_B": [[0.1]],
        "grad_A": [[0.3, -0.4]],
    }
    with tempfile.TemporaryDirectory() as d:
        inp = os.path.join(d, "input.json")
        outp = os.path.join(d, "out.json")
        with open(inp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        proc = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "..", "scripts", "lora_importance.py"), inp, "--output", outp], text=True, capture_output=True)
        assert proc.returncode == 0, proc.stderr
        result = json.load(open(outp, encoding="utf-8"))
        assert result["diagnostics"]["uses_base_gradients"] is False
        assert len(result["importance"][0]) == 2
