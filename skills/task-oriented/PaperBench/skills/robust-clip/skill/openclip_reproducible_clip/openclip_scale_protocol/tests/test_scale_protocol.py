import json
import tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from scale_protocol import build_scale_table

records = [{"dataset": "LAION-80M", "model": "ViT-B/32", "samples_seen": 10, "gmac_per_sample": 2, "accuracy": 75.0, "recall_at_5": 60.0}]
result = build_scale_table(records)
item = result["records"][0]
assert item["total_compute"] == 20.0
assert item["classification_error"] == 25.0
assert item["retrieval_error"] == 40.0
try:
    build_scale_table([{"dataset": "x", "model": "m", "samples_seen": 0, "gmac_per_sample": 1}])
    raise AssertionError("expected failure")
except ValueError:
    pass
