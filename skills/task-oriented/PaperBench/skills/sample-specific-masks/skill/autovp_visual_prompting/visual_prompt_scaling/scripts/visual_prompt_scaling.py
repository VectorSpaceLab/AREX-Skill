import math

def sigmoid(x): return 1/(1+math.exp(-x))

def prompt_width(source_size, target_size):
    if target_size > source_size: raise ValueError('target_size larger than source_size')
    return (source_size-target_size)//2

def frame_mask(source_size, target_size, channels=1):
    p=prompt_width(source_size,target_size)
    return [[[1 if r<p or r>=p+target_size or c<p or c>=p+target_size else 0 for c in range(source_size)] for r in range(source_size)] for _ in range(channels)]

def apply_prompt(image, source_size, prompt_value=0.0):
    target_size=len(image); p=prompt_width(source_size,target_size); mask=frame_mask(source_size,target_size,1)[0]
    canvas=[[0.0 for _ in range(source_size)] for _ in range(source_size)]
    for r in range(target_size):
        for c in range(target_size): canvas[p+r][p+c]=float(image[r][c])
    val=sigmoid(prompt_value)
    for r in range(source_size):
        for c in range(source_size):
            if mask[r][c]: canvas[r][c]=val
    return canvas
