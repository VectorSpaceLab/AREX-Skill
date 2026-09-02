import json

def _predicate_active(predicate, flags):
    if predicate in (None, '', 'always'):
        return True
    if predicate.startswith('not:'):
        return not bool(flags.get(predicate[4:], False))
    return bool(flags.get(predicate, False))

def select_strategy(memory, strategies, previous=None):
    flags = memory.get('derived_flags', {})
    active = [dict(s) for s in strategies if _predicate_active(str(s.get('predicate','always')), flags)]
    if not active:
        selected = {'name':'wait','priority':-1,'actions':[{'type':'wait'}]}
    else:
        selected = sorted(active, key=lambda s: (-int(s.get('priority',0)), str(s.get('name',''))))[0]
    interrupted = bool(previous and previous != selected['name'])
    return {'selected_strategy': selected['name'], 'interrupted': interrupted, 'interruption_reason': f'{selected["name"]}_priority' if interrupted else '', 'actions': selected.get('actions', [])}

def main():
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('memory'); p.add_argument('strategies'); p.add_argument('--previous'); p.add_argument('--output', required=True)
    a=p.parse_args(); res=select_strategy(json.load(open(a.memory)), json.load(open(a.strategies)), a.previous); json.dump(res, open(a.output,'w'), indent=2)
if __name__ == '__main__': main()
