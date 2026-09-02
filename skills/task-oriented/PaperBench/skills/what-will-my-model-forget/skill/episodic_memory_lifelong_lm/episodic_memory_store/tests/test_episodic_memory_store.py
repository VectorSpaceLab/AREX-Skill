import sys
sys.path.insert(0, 'scripts')
from memory_store import EpisodicMemory, frozen_bow_key
vocab=['cat','dog','finance']
assert frozen_bow_key('cat cat', vocab)==frozen_bow_key('cat cat', vocab)
mem=EpisodicMemory(vocab, seed=1)
mem.maybe_write({'text':'cat pet','label':'1'}); mem.maybe_write({'text':'finance market','label':'0'})
assert mem.knn('cat',1)[0]['label']=='1'
assert len(mem.sample(5))==2
empty = EpisodicMemory(vocab, seed=4)
assert empty.knn('cat', 3) == []
assert empty.sample(2) == []
