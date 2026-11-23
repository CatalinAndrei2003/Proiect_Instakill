from copy import deepcopy
from datetime import datetime, timezone
from app.feed.ranking import rank_feed

def test_order_tie_and_input_unchanged():
    posts=[{'post_id':3,'content':'c'},{'post_id':1,'content':'a'},{'post_id':2,'content':'b'}]
    original=deepcopy(posts); sig={1:{'x':1},2:{'x':1},3:{'x':.5}}
    result=rank_feed(posts,sig,datetime.now(timezone.utc),{'x':1},2)
    assert [p['post_id'] for p in result]==[1,2]
    assert posts==original

def test_deterministic():
    p=[{'post_id':i} for i in range(5)]; s={i:{'v':float(i%2)} for i in range(5)}
    a=rank_feed(p,s,None,{'v':1},3); b=rank_feed(p,s,None,{'v':1},3)
    assert a==b
