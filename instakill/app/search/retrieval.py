"""Pure cosine retrieval and deterministic top-k."""
import heapq, math

def cosine(a,b):
    if not a or len(a)!=len(b): return 0.0
    na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(x*x for x in b))
    if not na or not nb: return 0.0
    return sum(x*y for x,y in zip(a,b))/(na*nb)

def retrieve_top(query_vector, posts, vectors, limit):
    scored=[]
    for post, vector in zip(posts,vectors):
        scored.append({**post,'score':float(cosine(query_vector,vector))})
    return sorted(scored,key=lambda x:(-x['score'],x['post_id']))[:limit]
