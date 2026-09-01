
import math

def build_text_prompts(labels, template='This is a photo of a {label}'):
    return [template.format(label=str(label)) for label in labels]

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def norm(a): return math.sqrt(dot(a,a)) or 1.0

def cosine_logits(image_vec, text_vecs):
    return [dot(image_vec,t)/(norm(image_vec)*norm(t)) for t in text_vecs]

def softmax(xs):
    m=max(xs); ex=[math.exp(x-m) for x in xs]; s=sum(ex); return [x/s for x in ex]

def predict_label(image_vec, text_vecs, labels):
    logits=cosine_logits(image_vec,text_vecs); probs=softmax(logits)
    k=max(range(len(labels)), key=lambda i: probs[i])
    return {'label': labels[k], 'logits': logits, 'probabilities': probs}
