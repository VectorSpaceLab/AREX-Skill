import sys
from pathlib import Path
skill_dir = Path(__file__).resolve().parents[1]
paper_skill_dir = skill_dir.parent
sys.path.insert(0, str(skill_dir / 'scripts'))
sys.path.insert(0, str(paper_skill_dir / 'episodic_memory_store' / 'scripts'))
from replay_trainer import BinaryBagClassifier, train_stream
from memory_store import EpisodicMemory
vocab=['old','new']
stream=[{'text':'old','label':'0'},{'text':'old','label':'0'},{'text':'new','label':'1'},{'text':'new','label':'1'}]
mem=EpisodicMemory(vocab, seed=2)
model=BinaryBagClassifier(vocab)
events=train_stream(model, stream, mem, replay_interval=2, replay_size=1)
assert [e['step'] for e in events]==[2,4]
assert events[-1]['sample_count']==1
