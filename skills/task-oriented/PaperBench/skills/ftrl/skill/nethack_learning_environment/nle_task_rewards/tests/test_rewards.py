from rewards import clipped_reward, reward_transition

def test_staircase_reward_and_clip():
    prev={"agent":{"row":0,"col":0},"entities":[{"type":"staircase_down","char":">","row":0,"col":1}],"blstats":{"gold":0,"score":0}}
    nxt={"agent":{"row":0,"col":1},"entities":[],"blstats":{"gold":5,"score":10}}
    out=reward_transition(prev,nxt,{"action":"DOWN","invalid_penalty":0.0})
    assert out["components"]["staircase"]==100.0
    assert out["components"]["gold"]==5.0
    assert 0.7 < out["clipped_reward"] < 0.9
    assert clipped_reward(0.0)==0.0
