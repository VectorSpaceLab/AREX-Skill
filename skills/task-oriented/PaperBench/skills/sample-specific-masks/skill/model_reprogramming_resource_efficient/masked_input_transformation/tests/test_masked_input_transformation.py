from input_transform import transform, trainable_count

def test_transform_preserves_target_and_applies_mask():
    y=transform([1,2],5,[0,0,1,0,1],[9,9,.5,7,-.25])
    assert y==[1.0,2.0,0.5,0.0,-0.25]
    assert trainable_count([0,1,1])==2

def test_rejects_too_large_target():
    try: transform([1,2,3],2,[0,0],[0,0])
    except ValueError: return
    assert False
