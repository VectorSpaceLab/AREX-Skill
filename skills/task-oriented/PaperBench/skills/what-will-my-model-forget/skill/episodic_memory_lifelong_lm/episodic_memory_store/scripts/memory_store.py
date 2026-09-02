import math, random

def frozen_bow_key(text, vocabulary):
    counts=[0.0]*len(vocabulary)
    index={term:i for i,term in enumerate(vocabulary)}
    for token in text.lower().split():
        if token in index:
            counts[index[token]] += 1.0
    norm=math.sqrt(sum(v*v for v in counts)) or 1.0
    return [v/norm for v in counts]

class EpisodicMemory:
    def __init__(self, vocabulary, write_probability=1.0, seed=0):
        self.vocabulary=list(vocabulary)
        self.write_probability=write_probability
        self.random=random.Random(seed)
        self.entries=[]
    def maybe_write(self, example):
        if self.random.random() <= self.write_probability:
            entry={'key': frozen_bow_key(example['text'], self.vocabulary), 'value': dict(example)}
            self.entries.append(entry)
            return True
        return False
    def sample(self, size):
        if not self.entries:
            return []
        return [e['value'] for e in self.random.sample(self.entries, min(size, len(self.entries)))]
    def knn(self, text, k):
        query=frozen_bow_key(text, self.vocabulary)
        scored=[]
        for entry in self.entries:
            dist=sum((a-b)**2 for a,b in zip(query, entry['key']))
            scored.append((dist, entry['value']))
        return [value for _, value in sorted(scored, key=lambda item: item[0])[:k]]
