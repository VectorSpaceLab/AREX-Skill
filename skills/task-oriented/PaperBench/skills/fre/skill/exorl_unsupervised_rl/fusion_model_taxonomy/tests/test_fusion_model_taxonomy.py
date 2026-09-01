from taxonomy import classify_method

def test_attention_is_implicit():
    assert classify_method('self-attention learns global associations')['category']=='implicit'

def test_loss_rule_is_explicit():
    assert classify_method('handcrafted gradient loss and saliency rule')['category']=='explicit'


def test_hybrid_detected_for_balanced_terms():
    assert classify_method('attention global plus handcrafted loss rule')['category']=='hybrid'
