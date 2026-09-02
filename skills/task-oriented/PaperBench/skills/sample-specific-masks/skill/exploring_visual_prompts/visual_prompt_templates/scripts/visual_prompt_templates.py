
def zeros_like(image):
    return [[[0.0 for _ in row] for row in channel] for channel in image]

def shape(image):
    return (len(image), len(image[0]), len(image[0][0]))

def padding_mask(image, pad):
    c,h,w=shape(image)
    if pad < 0 or pad*2 >= min(h,w):
        raise ValueError('padding must leave a non-empty center')
    mask=zeros_like(image)
    for ch in range(c):
        for i in range(h):
            for j in range(w):
                if i < pad or i >= h-pad or j < pad or j >= w-pad:
                    mask[ch][i][j]=1.0
    return mask

def apply_padding_prompt(image, prompt, pad, clamp=None):
    c,h,w=shape(image)
    if shape(prompt)!=(c,h,w):
        raise ValueError('prompt shape must match image')
    mask=padding_mask(image,pad)
    out=zeros_like(image)
    for ch in range(c):
        for i in range(h):
            for j in range(w):
                val=image[ch][i][j]+mask[ch][i][j]*prompt[ch][i][j]
                if clamp is not None:
                    lo,hi=clamp; val=max(lo,min(hi,val))
                out[ch][i][j]=val
    return out, mask
