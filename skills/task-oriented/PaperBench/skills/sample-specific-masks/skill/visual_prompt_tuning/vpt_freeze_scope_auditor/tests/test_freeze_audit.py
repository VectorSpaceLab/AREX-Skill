from freeze_audit import audit
def test_backbone_change_fails():
    b={'backbone.w':[1,2], 'prompt.p':[0], 'head.w':[1]}
    a={'backbone.w':[1,3], 'prompt.p':[1], 'head.w':[2]}
    assert not audit(b,a)['ok']
    a['backbone.w']=[1,2]
    assert audit(b,a)['ok']

def test_trainable_ratio_counts_only_prompt_and_head():
    b={'backbone.a':[1,2,3,4], 'prompt.x':[0,0], 'head.y':[1]}
    a={'backbone.a':[1,2,3,4], 'prompt.x':[1,0], 'head.y':[2]}
    r=audit(b,a)
    assert r['ok'] and abs(r['trainable_ratio']-3/7)<1e-9
