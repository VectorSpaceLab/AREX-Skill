#!/usr/bin/env python3
"""Validate common DeepFace detection/demography arguments without building models."""
from __future__ import annotations
import argparse, base64, json
from pathlib import Path
DETECTORS={"opencv","mtcnn","ssd","dlib","retinaface","mediapipe","yolov8n","yolov8m","yolov8l","yolov11n","yolov11s","yolov11m","yolov11l","yolov12n","yolov12s","yolov12m","yolov12l","yunet","fastmtcnn","centerface","skip"}
ACTIONS={"emotion","age","gender","race"}
COLORS={"rgb","bgr","gray"}

def main()->int:
    ap=argparse.ArgumentParser(description='Static DeepFace detection/demography argument checker.')
    ap.add_argument('--image')
    ap.add_argument('--detector', default='opencv')
    ap.add_argument('--actions', default='emotion,age,gender,race')
    ap.add_argument('--color-face', default='rgb', choices=sorted(COLORS))
    ap.add_argument('--expand-percentage', type=int, default=0)
    ap.add_argument('--json', action='store_true')
    args=ap.parse_args()
    issues=[]
    if args.detector not in DETECTORS: issues.append(f'Unsupported detector: {args.detector}')
    actions=[a.strip() for a in args.actions.split(',') if a.strip()]; bad=[a for a in actions if a not in ACTIONS]
    if bad: issues.append(f'Unsupported actions: {bad}')
    if args.expand_percentage < 0: issues.append('expand_percentage cannot be negative; DeepFace overwrites negatives to 0 internally')
    image_info=None
    if args.image:
        if args.image.startswith('data:image/'):
            try:
                header,payload=args.image.split(',',1); base64.b64decode(payload, validate=True); image_info={'kind':'base64','header':header}
            except Exception as exc: issues.append(f'Invalid base64 image URI: {exc}')
        else:
            p=Path(args.image); image_info={'kind':'path','exists':p.exists(),'suffix':p.suffix.lower(),'ascii_path':str(p).isascii()}
            if p.suffix.lower() not in {'.jpg','.jpeg','.png'}: issues.append('DeepFace local folder utilities only treat jpg/jpeg/png as image files')
            if not str(p).isascii(): issues.append('DeepFace image path strings must be ASCII; pass a NumPy array for non-ASCII paths')
    report={'ok':not issues,'issues':issues,'detector':args.detector,'actions':actions,'color_face':args.color_face,'image':image_info}
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else ('OK' if report['ok'] else 'ISSUES\n- ' + '\n- '.join(issues)))
    return 0 if report['ok'] else 2
if __name__=='__main__': raise SystemExit(main())
