from decoding_policy import select_token
def test_greedy_selects_largest_logit():
    trace=select_token({"a":0,"b":3,"c":1},mode="greedy")
    assert trace["selected"]=="b"; assert trace["candidates"]==["b"]
def test_top_p_is_seeded_and_has_candidates():
    t1=select_token({"a":3,"b":2,"c":1},mode="top_p",top_p=0.95,seed=7)
    t2=select_token({"a":3,"b":2,"c":1},mode="top_p",top_p=0.95,seed=7)
    assert t1["selected"]==t2["selected"]; assert len(t1["candidates"])>=1
