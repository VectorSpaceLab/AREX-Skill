from update import train_one_step

def test_train_one_step_changes_params_and_reduces_loss():
    unroll={"features":[1.0,-0.5,0.25],"bootstrap_feature":0.0,"rewards":[1.0,0.0,0.5],"discounts":[0.9,0.9,0.0],"actions":[0,1,0],"behavior_action_probs":[0.45,0.40,0.55]}
    out=train_one_step({"policy_weight":0.1,"value_weight":0.0}, unroll, lr=0.05)
    assert out["params_before"] != out["params_after"]
    assert out["loss_after"] <= out["loss_before"]
