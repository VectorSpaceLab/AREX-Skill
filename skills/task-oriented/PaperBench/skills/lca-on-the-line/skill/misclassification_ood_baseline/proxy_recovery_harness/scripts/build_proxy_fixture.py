#!/usr/bin/env python3
import json

def fixture():
    labels=[1]*6 + [0]*6
    logits=[[5,1,0],[4.5,1,0],[4,1,0],[3.5,1,0],[3.2,1,0],[3,1,0], [1.2,1.1,1.0],[1.1,1.0,0.9],[0.8,0.7,0.6],[0.6,0.5,0.4],[0.3,0.2,0.1],[0.1,0.0,-0.1]]
    return {'dataset':'synthetic_softmax_ood_proxy','labels_in_positive':labels,'logits':logits,'is_resource_derived':False,'resource_files':[]}

def main():
    import argparse
    ap=argparse.ArgumentParser(); ap.add_argument('--output', required=True); args=ap.parse_args()
    json.dump(fixture(), open(args.output,'w'), indent=2)
if __name__ == '__main__': main()
