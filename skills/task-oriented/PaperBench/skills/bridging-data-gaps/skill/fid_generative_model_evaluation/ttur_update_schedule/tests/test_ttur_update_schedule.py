import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "ttur_schedule.py"
spec = importlib.util.spec_from_file_location("ttur_schedule", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

result = mod.run_ttur_saddle(steps=10, generator_lr=0.05, discriminator_lr=0.2)
assert result["diagnostics"]["separate_rates"] is True
assert result["diagnostics"]["optimizer_step_executed"] is True
assert result["loss_after"] < result["loss_before"]
assert result["trace"][0]["generator_lr"] != result["trace"][0]["discriminator_lr"]
