import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reduced_training_harness import one_step

batch = {"pairs":[{"latent_id":"z1","source_features":[1,0],"target_features":[0.6,0.4]}, {"latent_id":"z2","source_features":[0,1],"target_features":[0.4,0.6]}], "real_target_negatives":[{"features":[0.5,0.5]}]}
trace = one_step(batch)
assert trace["params_before"] != trace["params_after"]
assert trace["loss_after"] < trace["loss_before"]
