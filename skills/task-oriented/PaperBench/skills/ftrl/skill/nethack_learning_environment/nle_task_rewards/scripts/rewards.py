import math

def clipped_reward(reward):
    return math.tanh(reward/100.0)

def reward_transition(prev, nxt, action_record, task="staircase_gold_scout"):
    components={"invalid_action":action_record.get("invalid_penalty",0.0),"staircase":0.0,"gold":0.0,"scout":0.0,"score":0.0}
    if action_record.get("action")=="DOWN" and any(e.get("type")=="staircase_down" and e.get("row")==prev["agent"]["row"] and e.get("col")==prev["agent"]["col"]+1 for e in prev.get("entities",[])):
        components["staircase"]=100.0
    components["gold"]=max(0.0, float(nxt.get("blstats",{}).get("gold",0))-float(prev.get("blstats",{}).get("gold",0)))
    seen_prev={(e["row"],e["col"],e["char"]) for e in prev.get("entities",[])}
    seen_next={(e["row"],e["col"],e["char"]) for e in nxt.get("entities",[])}
    components["scout"]=float(len(seen_next-seen_prev))
    components["score"]=max(0.0, float(nxt.get("blstats",{}).get("score",0))-float(prev.get("blstats",{}).get("score",0)))
    total=sum(components.values())
    return {"components":components,"total_reward":total,"clipped_reward":clipped_reward(total),"terminal":components["staircase"]>0}
