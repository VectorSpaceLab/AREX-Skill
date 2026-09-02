from contrastive import symmetric_contrastive_loss, train_text_bias_proxy

def test_aligned_loss_below_shuffled_loss():
    imgs=[[1,0],[0,1]]
    aligned=[[1,0],[0,1]]
    shuffled=[[0,1],[1,0]]
    assert symmetric_contrastive_loss(imgs, aligned)["loss"] < symmetric_contrastive_loss(imgs, shuffled)["loss"]

def test_proxy_training_reduces_loss_and_changes_params():
    result=train_text_bias_proxy([[1,0],[0,1]], [[0.8,0.2],[0.2,0.8]], [0,1], steps=2, lr=0.05)
    assert result["loss_after"] < result["loss_before"]
    assert result["params_before"] != result["params_after"]
