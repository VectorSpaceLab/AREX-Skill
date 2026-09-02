import argparse, json, math

def label_from_completion(completion):
    text=str(completion).lower(); return 1 if any(t in text for t in ["yes","positive","true","entails","2"]) else 0

def features(record):
    text=(record.get("prompt","")+" "+record.get("completion","")).lower(); return [1.0, float("instruction" in text), float("because" in text or "therefore" in text), float("not" in text or "bad" in text)]

def sigmoid(v):
    if v >= 0: z=math.exp(-v); return 1/(1+z)
    z=math.exp(v); return z/(1+z)

def loss(records, params):
    total=0.0
    for r in records:
        x=features(r); y=label_from_completion(r.get("completion","")); p=sigmoid(sum(w*v for w,v in zip(params,x))); total += -(y*math.log(p+1e-12)+(1-y)*math.log(1-p+1e-12))
    return total/max(1,len(records))

def train(records, learning_rate=0.5, steps=3):
    params=[0.0,0.0,0.0,0.0]; before=list(params); loss_before=loss(records,params); step_losses=[]
    for _ in range(steps):
        grads=[0.0 for _ in params]
        for r in records:
            x=features(r); y=label_from_completion(r.get("completion","")); p=sigmoid(sum(w*v for w,v in zip(params,x)))
            for i,v in enumerate(x): grads[i] += (p-y)*v/max(1,len(records))
        params=[w-learning_rate*g for w,g in zip(params,grads)]; step_losses.append(loss(records,params))
    return {"loss_before":loss_before,"loss_after":loss(records,params),"params_before":before,"params_after":params,"step_losses":step_losses,"optimizer_step_executed": before != params,"reduced_training_executed": True,"full_model_training_executed": False}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--formatted", required=True); p.add_argument("--output", required=True); p.add_argument("--learning-rate", type=float, default=0.5); p.add_argument("--steps", type=int, default=3); a=p.parse_args()
    with open(a.formatted, encoding="utf-8") as h: records=json.load(h)
    with open(a.output,"w",encoding="utf-8") as h: json.dump(train(records,a.learning_rate,a.steps),h,indent=2,sort_keys=True)
if __name__ == "__main__": main()
