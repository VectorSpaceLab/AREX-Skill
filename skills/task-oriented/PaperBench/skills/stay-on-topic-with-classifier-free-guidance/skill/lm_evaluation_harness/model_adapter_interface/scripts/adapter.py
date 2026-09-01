class DeterministicLM:
    def __init__(self, scores=None, generations=None):
        self.scores=scores or {}; self.generations=generations or {}
    def loglikelihood(self, requests):
        out=[]
        for context, continuation in requests:
            score=self.scores.get((context, continuation), self.scores.get(continuation, -100.0))
            best=max([v for k,v in self.scores.items() if not isinstance(k,tuple) or k[0]==context] or [score])
            out.append((float(score), score==best))
        return out
    def loglikelihood_rolling(self, requests):
        return [(float(-len(str(r))),) for r in requests]
    def generate_until(self, requests):
        outs=[]
        for prompt, kwargs in requests:
            text=self.generations.get(prompt, prompt)
            for stop in kwargs.get('until',[]):
                if stop in text: text=text.split(stop)[0]
            outs.append(text[:kwargs.get('max_gen_toks', len(text))])
        return outs

def dispatch(adapter, request_type, requests):
    if request_type not in {'loglikelihood','loglikelihood_rolling','generate_until'}:
        raise ValueError('unsupported request_type')
    return getattr(adapter, request_type)(requests)
