import json

ENTITY_CHARS={">":"staircase_down","$":"gold","@":"agent",".":"floor","#":"corridor"}

def summarize_observation(obs):
    required=["chars","message","blstats"]
    missing=[k for k in required if k not in obs]
    if missing:
        raise ValueError("missing observation fields: "+",".join(missing))
    chars=obs["chars"]
    entities=[]
    agent=None
    for row,line in enumerate(chars):
        for col,ch in enumerate(line):
            if ch in ENTITY_CHARS:
                entities.append({"type":ENTITY_CHARS[ch],"char":ch,"row":row,"col":col})
                if ch=="@": agent={"row":row,"col":col}
    if agent is None:
        raise ValueError("agent marker @ not found")
    return {"height":len(chars),"width":max(len(x) for x in chars),"agent":agent,"entities":entities,"message":obs["message"],"blstats":obs["blstats"]}

def main():
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('--output',required=True)
    a=p.parse_args(); data=json.load(open(a.input)); out=summarize_observation(data)
    json.dump(out, open(a.output,'w'), indent=2)
if __name__=='__main__': main()
