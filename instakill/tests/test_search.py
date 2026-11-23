from app.search.retrieval import retrieve_top

def test_cosine_topk_and_tie_break():
    posts=[{'post_id':2,'content':'second'},{'post_id':1,'content':'first'},{'post_id':3,'content':'third'}]
    vectors=[[1.0,0.0],[1.0,0.0],[0.0,1.0]]
    result=retrieve_top([1.0,0.0],posts,vectors,2)
    assert [p['post_id'] for p in result]==[1,2]
    assert result[0]['score']==1.0
