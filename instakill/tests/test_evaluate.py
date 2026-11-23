import math
import sqlite3
from scripts.evaluate import ndcg_at_10, create_snapshot

def test_ndcg_cases():
    assert ndcg_at_10([1,2],set())==0
    assert ndcg_at_10([1,2,3],{1,2})==1
    assert abs(ndcg_at_10([8,9,7,4],{4})-1/math.log2(5))<1e-9

def test_snapshot_no_future_rows(tmp_path):
    src=tmp_path/'src.db'; dst=tmp_path/'copy.db'; c=sqlite3.connect(src)
    c.executescript('CREATE TABLE "like"(user_id INTEGER,post_id INTEGER,created_at TEXT); CREATE TABLE post(id INTEGER PRIMARY KEY,created_at TEXT); CREATE TABLE follow(created_at TEXT);')
    c.execute('INSERT INTO post VALUES (1,"2020-01-01")'); c.execute('INSERT INTO post VALUES (2,"2022-01-01")')
    c.execute('INSERT INTO "like" VALUES (1,1,"2020-01-01")'); c.execute('INSERT INTO "like" VALUES (1,2,"2020-01-01")'); c.execute('INSERT INTO "like" VALUES (1,1,"2022-01-01")')
    c.execute('INSERT INTO follow VALUES ("2020-01-01")'); c.execute('INSERT INTO follow VALUES ("2022-01-01")')
    c.commit(); c.close(); create_snapshot(src,dst,'2021-01-01')
    c=sqlite3.connect(dst)
    assert c.execute('SELECT COUNT(*) FROM post').fetchone()[0]==1
    assert c.execute('SELECT COUNT(*) FROM "like"').fetchone()[0]==1
    assert c.execute('SELECT COUNT(*) FROM "like" WHERE post_id=2').fetchone()[0]==0
    assert c.execute('SELECT COUNT(*) FROM follow').fetchone()[0]==1

def test_evaluator_uses_feed_service(tmp_path, monkeypatch):
    from app.db.database import init_db, get_connection
    from app.feed.service import FeedService
    from scripts.evaluate import evaluate
    db=tmp_path/'eval.db'; init_db(db)
    with get_connection(db) as c:
        c.execute("INSERT INTO user(id,username,created_at) VALUES (1,'reader','2025-01-01T00:00:00Z')")
        c.execute("INSERT INTO user(id,username,created_at) VALUES (2,'author','2025-01-01T00:00:00Z')")
        for i in range(1,5): c.execute('INSERT INTO post(id,user_id,content,created_at) VALUES (?,?,?,?)',(i,2,f'post{i}','2025-01-01T00:00:00Z'))
        for i in range(1,4): c.execute('INSERT INTO "like"(user_id,post_id,created_at) VALUES (1,?,?)',(i,'2025-01-02T00:00:00Z'))
        c.execute('INSERT INTO "like"(user_id,post_id,created_at) VALUES (1,4,?)',('2025-01-11T00:00:00Z',))
        c.execute('INSERT INTO follow(follower_id,followed_id,created_at) VALUES (1,2,?)',('2025-01-01T00:00:00Z',))
    calls={'n':0}; original=FeedService.get_feed
    def counted(self,*args,**kwargs): calls['n']+=1; return original(self,*args,**kwargs)
    monkeypatch.setattr(FeedService,'get_feed',counted)
    evaluate(str(db),'2025-01-10T00:00:00Z',42,tmp_path/'out')
    assert calls['n']==3  # chronological, for_you, learned; popularity is eval-only

def test_eval_csv_is_deterministic(tmp_path):
    from app.db.database import init_db, get_connection
    from scripts.evaluate import evaluate
    db=tmp_path/'repeat.db'; init_db(db)
    with get_connection(db) as c:
        c.execute("INSERT INTO user(id,username,created_at) VALUES (1,'reader','2025-01-01T00:00:00Z')")
        c.execute("INSERT INTO user(id,username,created_at) VALUES (2,'author','2025-01-01T00:00:00Z')")
        for i in range(1,5): c.execute('INSERT INTO post(id,user_id,content,created_at) VALUES (?,?,?,?)',(i,2,f'post{i}','2025-01-01T00:00:00Z'))
        for i in range(1,4): c.execute('INSERT INTO "like"(user_id,post_id,created_at) VALUES (1,?,?)',(i,'2025-01-02T00:00:00Z'))
        c.execute('INSERT INTO "like"(user_id,post_id,created_at) VALUES (1,4,?)',('2025-01-11T00:00:00Z',))
        c.execute('INSERT INTO follow(follower_id,followed_id,created_at) VALUES (1,2,?)',('2025-01-01T00:00:00Z',))
    out1=tmp_path/'run1'; out2=tmp_path/'run2'
    evaluate(str(db),'2025-01-10T00:00:00Z',42,out1)
    evaluate(str(db),'2025-01-10T00:00:00Z',42,out2)
    assert (out1/'eval_results.csv').read_bytes()==(out2/'eval_results.csv').read_bytes()
