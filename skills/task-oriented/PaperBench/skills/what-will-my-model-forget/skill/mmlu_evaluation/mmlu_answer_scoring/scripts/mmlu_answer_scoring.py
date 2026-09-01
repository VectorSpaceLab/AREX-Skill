import json, argparse, re
LABELS=("A","B","C","D")
def extract_label(prediction):
    text=str(prediction).strip().upper()
    m=re.search(r"(?:ANSWER\s*[:IS]*\s*)?\(?([ABCD])\)?", text)
    return m.group(1) if m else ""
def score_predictions(predictions, labels, confidences=None):
    records=[]; correct=0
    for i,(p,g) in enumerate(zip(predictions, labels)):
        pred=extract_label(p); gold=extract_label(g); ok=pred==gold and pred in LABELS; correct+=int(ok)
        rec={"index":i,"prediction":pred,"gold":gold,"correct":ok}
        if confidences is not None: rec["confidence"]=float(confidences[i])
        records.append(rec)
    acc=correct/len(records) if records else 0.0
    gap=None
    if confidences is not None and records:
        gap=abs(sum(float(c) for c in confidences)/len(records)-acc)
    return {"accuracy":acc,"count":len(records),"records":records,"calibration_gap":gap}
def main():
    p=argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('--output',required=True); a=p.parse_args()
    data=json.loads(open(a.input).read()); out=score_predictions(data['predictions'],data['labels'],data.get('confidences')); open(a.output,'w').write(json.dumps(out,indent=2)+"\n")
if __name__=='__main__': main()
