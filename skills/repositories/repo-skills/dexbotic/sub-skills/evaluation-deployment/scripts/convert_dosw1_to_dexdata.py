#!/usr/bin/env python3
"""Safe, data-only DOS-W1 Table30v2 episode converter.

It reads JSON state/video metadata and writes DexData JSONL. It never opens a
camera, serial device, robot SDK, network bridge, or actuator.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path

def read_json(path): return json.loads(path.read_text(encoding="utf-8"))
def read_jsonl(path): return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

def joints(d):
    x=d.get("joint_positions")
    if not isinstance(x,list) or len(x)!=6: raise ValueError("joint_positions must contain 6 values")
    return [float(v) for v in x]

def grip(d):
    for k in ("gripper_width","gripper"):
        if k in d:return float(d[k])
    raise ValueError("missing gripper_width/gripper")

def valid(s,gmin,gmax):
    return all(math.isfinite(x) for x in s) and all(-math.pi<=x<=math.pi for x in s[:6]+s[7:13]) and all(gmin<=s[i]<=gmax for i in (6,13))

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("--task-dir",type=Path,required=True); ap.add_argument("--output-dir",type=Path,required=True); ap.add_argument("--prompt",required=True); ap.add_argument("--max-episodes",type=int); ap.add_argument("--keep-static",action="store_true"); a=ap.parse_args()
    episodes=sorted(p for p in (a.task_dir/"data").iterdir() if p.is_dir())
    if a.max_episodes is not None: episodes=episodes[:a.max_episodes]
    out=a.output_dir/a.task_dir.name; out.mkdir(parents=True,exist_ok=True); total=0; written=0
    cameras={"images_1":"cam_high_rgb.mp4","images_2":"cam_left_wrist_rgb.mp4","images_3":"cam_right_wrist_rgb.mp4"}
    for ep in episodes:
        try:
            meta=read_json(ep/"meta"/"episode_meta.json"); left=read_jsonl(ep/"states"/"left_states.jsonl"); right=read_jsonl(ep/"states"/"right_states.jsonl")
            n=min(int(meta.get("frames",len(left))),len(left),len(right)); recs=[]; previous=None
            for i in range(n):
                s=joints(left[i])+[grip(left[i])]+joints(right[i])+[grip(right[i])]
                if not valid(s,-1e-3,8e-2): continue
                if previous is not None and not a.keep_static:
                    same=all(abs(s[j]-previous[j])<=5e-4 for j in list(range(6))+list(range(7,13))) and abs(s[6]-previous[6])<=1e-3 and abs(s[13]-previous[13])<=1e-3
                    if same: continue
                rec={"state":s,"prompt":a.prompt,"is_robot":True,"extra":{"episode":ep.name,"frame_idx":i}}
                for key,name in cameras.items(): rec[key]={"type":"video","url":str((ep/"videos"/name).relative_to(a.task_dir)),"frame_idx":i}
                recs.append(rec); previous=s
            if recs:
                (out/f"episode_{written:05d}.jsonl").write_text("".join(json.dumps(r)+"\n" for r in recs),encoding="utf-8"); written+=1; total+=len(recs)
        except Exception as e: print(json.dumps({"episode":ep.name,"error":str(e)}))
    print(json.dumps({"episodes":written,"records":total,"output":str(out)},indent=2))
if __name__=="__main__":main()
