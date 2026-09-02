
import math, random

def matmul(A,B):
    return [[sum(A[i][k]*B[k][j] for k in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]

def transpose(A): return [list(row) for row in zip(*A)]
def matvec(A,x): return [sum(a*b for a,b in zip(row,x)) for row in A]
def add(u,v): return [a+b for a,b in zip(u,v)]
def outer(u,v): return [[a*b for b in v] for a in u]
def zeros(m,n): return [[0.0]*n for _ in range(m)]
def rank_leq(matrix, r, tol=1e-9):
    A=[row[:] for row in matrix]; m=len(A); n=len(A[0]) if m else 0; rank=0; row=0
    for col in range(n):
        piv=None
        for i in range(row,m):
            if abs(A[i][col])>tol: piv=i; break
        if piv is None: continue
        A[row],A[piv]=A[piv],A[row]
        pv=A[row][col]
        A[row]=[x/pv for x in A[row]]
        for i in range(m):
            if i!=row and abs(A[i][col])>tol:
                fac=A[i][col]; A[i]=[a-fac*b for a,b in zip(A[i],A[row])]
        rank+=1; row+=1
        if row==m: break
    return rank <= r, rank

class LoRALinear:
    def __init__(self, weight, r=1, alpha=1.0, seed=0, A=None, B=None):
        self.weight=[row[:] for row in weight]; self.r=r; self.alpha=alpha; self.scaling=(alpha/r) if r else 0.0
        rnd=random.Random(seed); in_f=len(weight[0]); out_f=len(weight)
        self.A = A if A is not None else [[rnd.uniform(-0.1,0.1) for _ in range(in_f)] for _ in range(r)]
        self.B = B if B is not None else [[0.0 for _ in range(r)] for _ in range(out_f)]
    def delta(self):
        if self.r<=0: return zeros(len(self.weight), len(self.weight[0]))
        return [[self.scaling*x for x in row] for row in matmul(self.B,self.A)]
    def merged_weight(self):
        D=self.delta(); return [[w+d for w,d in zip(wr,dr)] for wr,dr in zip(self.weight,D)]
    def forward(self,x, merged=False):
        W=self.merged_weight() if merged else self.weight
        y=matvec(W,x)
        if not merged and self.r>0:
            ax=matvec(self.A,x); bax=matvec(self.B,ax); y=add(y,[self.scaling*v for v in bax])
        return y

def lora_parameter_count(d_model, r, matrices):
    return 2 * matrices * d_model * r

def loss_reduction_fraction(before, after):
    return 0.0 if before == 0 else (before-after)/before

def validate_trace(trace, min_reduction=0.0):
    reduction=loss_reduction_fraction(trace['loss_before'], trace['loss_after'])
    return {'loss_reduction_fraction':reduction,'passes': reduction >= min_reduction and trace.get('params_before') != trace.get('params_after')}
