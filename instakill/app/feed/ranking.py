"""Pure feed ranking. Heap-based top-k, deterministic post_id tie-break."""
import heapq, math

def rank_feed(candidates, signals, now, weights, limit):
    # Inputs are read-only; each row is copied before adding score.
    heap=[]
    for post in candidates:
        pid=int(post['post_id']); s=signals.get(pid,{})
        score=sum(float(weights.get(name,0.0))*float(value) for name,value in s.items())
        item={**post,'score':float(score)}
        # min heap retains best k; tie: lower post_id ranks ahead
        key=(score,-pid)
        if len(heap)<limit: heapq.heappush(heap,(key,item))
        elif key>heap[0][0]: heapq.heapreplace(heap,(key,item))
    return [item for _,item in sorted(heap,key=lambda pair:(-pair[0][0],-pair[0][1]))]

def build_signals(candidates, followed_authors, liked_authors, now):
    signals={}
    for p in candidates:
        try:
            from datetime import datetime, timezone
            created=datetime.fromisoformat(str(p['created_at']).replace('Z','+00:00'))
            current=now if now.tzinfo else now.replace(tzinfo=timezone.utc)
            age=max(0.0,(current-created).total_seconds()/3600)
        except Exception: age=24*365
        freshness=math.exp(-age/24.0)
        author=int(p['user_id'])
        affinity=1.0 if author in followed_authors else (0.5 if author in liked_authors else 0.0)
        popularity=math.log1p(max(0,int(p.get('likes',0))))/math.log(101)
        signals[int(p['post_id'])]={'freshness':freshness,'affinity':affinity,'popularity':min(1.0,popularity)}
    return signals
