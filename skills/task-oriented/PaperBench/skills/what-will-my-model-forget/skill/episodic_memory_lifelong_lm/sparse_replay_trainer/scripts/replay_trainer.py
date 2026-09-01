import math

def sigmoid(x):
    return 1.0/(1.0+math.exp(-max(min(x, 30), -30)))

class BinaryBagClassifier:
    def __init__(self, vocabulary):
        self.vocabulary=list(vocabulary)
        self.weights=[0.0]*len(vocabulary)
        self.bias=0.0
    def features(self, text):
        return [1.0 if term in text.lower().split() else 0.0 for term in self.vocabulary]
    def score(self, text, weights=None, bias=None):
        weights=self.weights if weights is None else weights
        bias=self.bias if bias is None else bias
        return sum(w*x for w,x in zip(weights, self.features(text))) + bias
    def predict(self, text, weights=None, bias=None):
        return 1 if sigmoid(self.score(text, weights, bias)) >= 0.5 else 0
    def update(self, example, lr=0.2):
        x=self.features(example['text']); y=int(example['label'])
        p=sigmoid(sum(w*v for w,v in zip(self.weights,x))+self.bias)
        grad=p-y
        self.weights=[w-lr*grad*v for w,v in zip(self.weights,x)]
        self.bias -= lr*grad
        return -(y*math.log(max(p,1e-9))+(1-y)*math.log(max(1-p,1e-9)))

def train_stream(model, stream, memory, replay_interval=4, replay_size=2, lr=0.2):
    events=[]
    for step, example in enumerate(stream, start=1):
        if step % replay_interval == 0:
            batch=memory.sample(replay_size)
            losses=[model.update(item, lr=lr) for item in batch]
            events.append({'step': step, 'sample_count': len(batch), 'losses': losses})
        model.update(example, lr=lr)
        memory.maybe_write(example)
    return events
