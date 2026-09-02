from tiny_vpt_train import train
def test_loss_decreases_and_backbone_frozen():
    tr=train([([0,0],0),([1,1],1)], [[0.01,0.0]], [0.1,0.1], [[1,0],[0,1]], steps=5)
    assert tr['loss_after'] < tr['loss_before']
    assert tr['params_after']['backbone']==tr['params_before']['backbone']

def test_zero_steps_keeps_parameters():
    tr=train([([0,0],0),([1,1],1)], [[0.01,0.0]], [0.1,0.1], [[1,0],[0,1]], steps=0)
    assert tr['params_after']==tr['params_before']
