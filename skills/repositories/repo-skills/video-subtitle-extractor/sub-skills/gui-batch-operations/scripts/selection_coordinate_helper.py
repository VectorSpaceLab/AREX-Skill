#!/usr/bin/env python3
"""Convert VSE GUI normalized selection rectangles to video pixel coordinates."""
from __future__ import annotations
import argparse, json

def convert(rect, frame_w, frame_h, preview_w, preview_h, border_left=0.0, border_top=0.0, scaled_w=1.0, scaled_h=1.0):
    ymin,ymax,xmin,xmax=rect
    x_adj=max(0.0, xmin-border_left); y_adj=max(0.0, ymin-border_top)
    w_adj=min(xmax-xmin, scaled_w-x_adj); h_adj=min(ymax-ymin, scaled_h-y_adj)
    scale_x=frame_w/(scaled_w*preview_w); scale_y=frame_h/(scaled_h*preview_h)
    pxmin=round(x_adj*scale_x*preview_w); pxmax=round((x_adj+w_adj)*scale_x*preview_w)
    pymin=round(y_adj*scale_y*preview_h); pymax=round((y_adj+h_adj)*scale_y*preview_h)
    pxmin=max(0,min(pxmin,frame_w)); pxmax=max(0,min(pxmax,frame_w))
    pymin=max(0,min(pymin,frame_h)); pymax=max(0,min(pymax,frame_h))
    if pxmin>pxmax: pxmin,pxmax=pxmax,pxmin
    if pymin>pymax: pymin,pymax=pymax,pymin
    return {'ymin':pymin,'ymax':pymax,'xmin':pxmin,'xmax':pxmax,'cli_order':[pymin,pymax,pxmin,pxmax]}

def main() -> int:
    ap=argparse.ArgumentParser(description='Convert normalized VSE GUI rectangle to video pixel coordinates.')
    ap.add_argument('--rect', nargs=4, type=float, required=True, metavar=('YMIN','YMAX','XMIN','XMAX'))
    ap.add_argument('--frame-width', type=int, required=True)
    ap.add_argument('--frame-height', type=int, required=True)
    ap.add_argument('--preview-width', type=int, default=960)
    ap.add_argument('--preview-height', type=int, default=540)
    ap.add_argument('--border-left', type=float, default=0.0)
    ap.add_argument('--border-top', type=float, default=0.0)
    ap.add_argument('--scaled-width', type=float, default=1.0)
    ap.add_argument('--scaled-height', type=float, default=1.0)
    ap.add_argument('--json', action='store_true')
    args=ap.parse_args()
    out=convert(args.rect,args.frame_width,args.frame_height,args.preview_width,args.preview_height,args.border_left,args.border_top,args.scaled_width,args.scaled_height)
    if args.json: print(json.dumps(out, indent=2))
    else: print('CLI subtitle area (ymin ymax xmin xmax):', *out['cli_order'])
    return 0
if __name__=='__main__':
    raise SystemExit(main())
