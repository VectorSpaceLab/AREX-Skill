import math, re


def tokens(text): return re.findall(r"[a-z]+", text.lower())

def build_vocab(records):
    vocab={}
    for r in records:
        for tok in tokens(r['source']):
            if tok not in vocab: vocab[tok]=len(vocab)
    return vocab

def featurize(text, vocab):
    x=[0.0]*len(vocab)
    for tok in tokens(text):
        if tok in vocab: x[vocab[tok]]+=1.0
    return x

def softmax(scores):
    m=max(scores); ex=[math.exp(s-m) for s in scores]; z=sum(ex); return [e/z for e in ex]

def train(records, labels, lr=0.3, epochs=20):
    vocab=build_vocab(records); W=[[0.0]*len(vocab) for _ in labels]; lab={l:i for i,l in enumerate(labels)}
    def loss():
        total=0.0
        for r in records:
            x=featurize(r['source'], vocab); probs=softmax([sum(wi*xi for wi,xi in zip(w,x)) for w in W]); total-=math.log(max(probs[lab[r['target']]],1e-12))
        return total/len(records)
    before=[row[:] for row in W]; loss_before=loss()
    for _ in range(epochs):
        for r in records:
            x=featurize(r['source'], vocab); probs=softmax([sum(wi*xi for wi,xi in zip(w,x)) for w in W]); yi=lab[r['target']]
            for k in range(len(labels)):
                grad=(probs[k]-(1 if k==yi else 0))
                for j,xi in enumerate(x): W[k][j]-=lr*grad*xi
    loss_after=loss()
    return {'labels':labels,'vocab':vocab,'params_before':before,'params_after':W,'loss_before':loss_before,'loss_after':loss_after}

def predict(model, source):
    x=featurize(source, model['vocab']); scores=[sum(wi*xi for wi,xi in zip(w,x)) for w in model['params_after']]
    return model['labels'][max(range(len(scores)), key=lambda i:scores[i])]
