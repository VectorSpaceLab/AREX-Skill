import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from intra_lpips_proxy_evaluation import intra_cluster_proxy

result = intra_cluster_proxy(
    [{"features":[0,0]}, {"features":[0,2]}, {"features":[10,0]}, {"features":[10,4]}],
    [{"features":[0,0]}, {"features":[10,0]}]
)
assert abs(result["intra_cluster_proxy"] - 3.0) < 1e-9
collapsed = intra_cluster_proxy([{"features":[0,0]}, {"features":[0,0]}], [{"features":[0,0]}])
assert collapsed["intra_cluster_proxy"] == 0.0
