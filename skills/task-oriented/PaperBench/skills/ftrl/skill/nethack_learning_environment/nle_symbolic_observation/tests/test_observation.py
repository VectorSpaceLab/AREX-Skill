from observation import summarize_observation

def test_extracts_agent_and_entities():
    obs={"chars":[".....",".@>$.","....."],"message":"You descend.","blstats":{"score":0}}
    out=summarize_observation(obs)
    assert out["agent"]=={"row":1,"col":1}
    assert any(e["type"]=="staircase_down" for e in out["entities"])
    assert any(e["type"]=="gold" for e in out["entities"])

def test_requires_agent():
    try:
        summarize_observation({"chars":["..."] ,"message":"","blstats":{}})
    except ValueError as exc:
        assert "agent" in str(exc)
    else:
        raise AssertionError("expected missing agent error")
