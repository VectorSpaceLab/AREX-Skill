from metrics import fusion_metrics

def test_metrics_numeric():
    ir=[[0,1],[0,1]]; vis=[[0,0.5],[0.5,1]]; fused=[[0,0.8],[0.4,1]]
    m=fusion_metrics(ir,vis,fused,[fused,fused])
    assert m['fusion_proxy_score']>0
    assert m['stability']==1.0


def test_degraded_stability_below_perfect():
    ir=[[0,1],[1,0]]; vis=[[0,0],[1,1]]; good=[[0,1],[1,0]]; bad=[[0,0],[0,0]]
    assert fusion_metrics(ir,vis,good,[good,bad])['stability'] < 1.0
