import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

def test_skill_smoke():
    from lora_linear import train, forward, init_lora
    W=[[1.0,0.0],[0.0,1.0]]; ex=[([1.0,2.0],[1.5,2.0]),([2.0,1.0],[3.0,1.0])]
    A,B=init_lora(2,2,1); assert forward(W,A,B,[1,2])==[1.0,2.0]
    tr=train(W,ex,steps=10,lr=0.2); assert tr['W0_unchanged']; assert tr['loss_after'] < tr['loss_before']


def test_initial_zero_b_preserves_base_multiple_inputs():
    from lora_linear import init_lora, forward
    W=[[2.0,1.0],[0.0,-1.0]]; A,B=init_lora(2,2,1)
    for x in ([0.0,0.0],[3.0,-1.0],[-2.0,4.0]):
        assert forward(W,A,B,list(x)) == [sum(W[i][j]*x[j] for j in range(2)) for i in range(2)]
