#!/usr/bin/env python3
import argparse, json

CANDIDATE_MARKERS = ['c_proj.weight','fc2.weight','w_out','W_out','down_proj.weight','mlp_out']

def _is_matrix(x): return isinstance(x, list) and x and all(isinstance(r, list) and r for r in x)
def _transpose(m): return [list(col) for col in zip(*m)]

def likely_output_name(name):
    low=name.lower()
    return any(marker.lower() in low for marker in CANDIDATE_MARKERS) or ('mlp' in low and ('proj' in low or 'out' in low))

def extract_from_matrix(matrix, source_name='matrix', orientation='neurons_by_rows', layer='layer0'):
    if not _is_matrix(matrix):
        raise ValueError('matrix must be a non-empty 2D list')
    if len({len(r) for r in matrix}) != 1:
        raise ValueError('matrix rows must have equal length')
    rows = matrix if orientation == 'neurons_by_rows' else _transpose(matrix)
    return {'orientation': orientation, 'residual_dim': len(rows[0]), 'vectors': [
        {'layer': layer, 'neuron': i, 'source_name': source_name, 'vector': [float(v) for v in row]} for i,row in enumerate(rows)
    ]}

def extract_from_state_dict(state, orientation_hint=None):
    if not isinstance(state, dict): raise ValueError('state must be a dict')
    found=[]
    for name, matrix in state.items():
        if _is_matrix(matrix) and likely_output_name(name):
            orientation = orientation_hint or 'neurons_by_columns'
            found.append(extract_from_matrix(matrix, name, orientation, name.split('.')[0]))
    if not found: raise ValueError('no likely FFN output projection matrices found')
    vectors=[]
    for item in found: vectors.extend(item['vectors'])
    return {'orientation': found[0]['orientation'], 'matrix_count': len(found), 'vectors': vectors}

def fixture():
    state={'blocks.0.mlp.c_proj.weight': [[1,0,0],[0,1,0]]}
    return extract_from_state_dict(state)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input')
    ap.add_argument('--output')
    ap.add_argument('--fixture', action='store_true')
    ap.add_argument('--orientation', choices=['neurons_by_rows','neurons_by_columns'])
    ns=ap.parse_args()
    out = fixture() if ns.fixture else extract_from_state_dict(json.load(open(ns.input)), ns.orientation)
    text=json.dumps(out, indent=2)
    if ns.output: open(ns.output,'w').write(text)
    else: print(text)
if __name__=='__main__': main()
