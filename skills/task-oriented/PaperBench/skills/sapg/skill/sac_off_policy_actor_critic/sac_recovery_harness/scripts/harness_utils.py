import json

def build_replay_batch():
    return {"states":[-1.0,-0.5,0.0,0.5,1.0,1.5],"actions":[-0.8,-0.3,0.1,0.4,0.9,1.1],"rewards":[0.2,0.4,0.7,0.8,1.0,0.6],"dones":[False,False,False,False,False,True],"log_probs":[-0.9,-0.8,-0.7,-0.6,-0.5,-0.4]}

def summarize_batch(batch):
    return {"sample_count": len(batch['rewards']), "reward_mean": sum(batch['rewards'])/len(batch['rewards']), "has_terminal": any(batch['dones'])}
