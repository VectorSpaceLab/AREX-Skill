import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from latent_pair_protocol import build_latent_pair_batch

batch = build_latent_pair_batch(
    [{"latent_id":"z1","features":[1,0]}, {"latent_id":"z2","features":[0,1]}],
    [{"latent_id":"z2","features":[0.1,0.9]}, {"latent_id":"z1","features":[0.9,0.1]}],
    [{"id":"r1","features":[1,1]}],
)
assert batch["latent_count"] == 2
assert batch["pairs"][0]["latent_id"] == "z1"
try:
    build_latent_pair_batch([{"latent_id":"z1","features":[1]}], [], [{"features":[0]}])
    raise AssertionError("expected mismatch failure")
except ValueError as exc:
    assert "match" in str(exc)
