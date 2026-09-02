import sys
from pathlib import Path
skill_dir = Path(__file__).resolve().parents[1]
paper_skill_dir = skill_dir.parent
sys.path.insert(0, str(skill_dir / 'scripts'))
sys.path.insert(0, str(paper_skill_dir / 'sparse_replay_trainer' / 'scripts'))
sys.path.insert(0, str(paper_skill_dir / 'episodic_memory_store' / 'scripts'))
from replay_trainer import BinaryBagClassifier
from memory_store import EpisodicMemory
from local_adaptation import adapt_and_predict
vocab=['old','new']
model=BinaryBagClassifier(vocab)
mem=EpisodicMemory(vocab, seed=3)
mem.maybe_write({'text':'old','label':'0'}); mem.maybe_write({'text':'new','label':'1'})
result=adapt_and_predict(model, mem, 'new', k=1, steps=2)
assert result['base_reset_confirmed']
assert result['local_weights'] != result['base_weights']
assert result['prediction'] in (0,1)
assert len(result['trace']) == 2
assert all('loss' in row for row in result['trace'])
assert model.weights == result['base_weights']
