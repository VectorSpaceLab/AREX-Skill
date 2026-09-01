import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from dual_contrastive_loss import dcl_loss

aligned = {"pairs":[{"latent_id":"z1","source_features":[1,0],"target_features":[1,0]}, {"latent_id":"z2","source_features":[0,1],"target_features":[0,1]}], "real_target_negatives":[{"features":[0.5,0.5]}]}
shuffled = {"pairs":[{"latent_id":"z1","source_features":[1,0],"target_features":[0,1]}, {"latent_id":"z2","source_features":[0,1],"target_features":[1,0]}], "real_target_negatives":[{"features":[0.5,0.5]}]}
a = dcl_loss(aligned)
s = dcl_loss(shuffled)
assert a["loss"] < s["loss"]
assert a["mechanism_checks"]["real_target_negatives_used"] is True
