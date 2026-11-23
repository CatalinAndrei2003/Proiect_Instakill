"""Deterministic demo seeder; replace with course MovieLens data for formal evaluation."""
from datetime import datetime, timedelta, timezone
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db.database import init_db, get_connection
USERS=[f'user{i:02d}' for i in range(1,16)]
TOPICS=['machine learning and neural networks','python programming tips','unity game development','campus life and study','movie recommendations','software engineering','computer architecture','AI research project','gaming news','data science experiment']
def seed():
    init_db()
    with get_connection() as c:
        for u in USERS: c.execute('INSERT OR IGNORE INTO user(username,created_at) VALUES (?,?)',(u,'2025-01-01T00:00:00Z'))
        ids={r['username']:r['id'] for r in c.execute('SELECT id,username FROM user')}
        if c.execute('SELECT COUNT(*) FROM post').fetchone()[0]<100:
            start=datetime(2025,1,19,tzinfo=timezone.utc)
            for i in range(100):
                stamp=(start+timedelta(minutes=i*10)).strftime('%Y-%m-%dT%H:%M:%SZ')
                c.execute('INSERT INTO post(user_id,content,created_at) VALUES (?,?,?)',(ids[USERS[i%len(USERS)]],f'Post {i}: {TOPICS[i%len(TOPICS)]} — sharing notes and ideas.',stamp))
        posts=[r['id'] for r in c.execute('SELECT id FROM post ORDER BY id')]
        # Normalize the original starter's six demo posts into the historical window.
        c.execute('UPDATE post SET created_at=? WHERE id <= 6',('2025-01-01T00:00:00Z',))
        for uid in ids.values():
            for author in ids.values():
                if uid!=author: c.execute('INSERT OR IGNORE INTO follow(follower_id,followed_id,created_at) VALUES (?,?,?)',(uid,author,'2025-01-01T00:00:00Z'))
        # Rebuild deterministic historical interactions for the demo corpus.
        c.execute('DELETE FROM "like"')
        post_authors={r['id']:r['user_id'] for r in c.execute('SELECT id,user_id FROM post')}
        for uid in ids.values():
            eligible=[pid for pid in posts if post_authors.get(pid)!=uid]
            # Ten known likes before T, then three held-out likes on posts already created.
            train=eligible[(uid*3)%len(eligible):]+eligible[:(uid*3)%len(eligible)]
            train=train[:10]
            held=[pid for pid in sorted(eligible,reverse=True) if pid not in train][:3]
            for j,pid in enumerate(train):
                stamp=(datetime(2025,1,10,tzinfo=timezone.utc)+timedelta(minutes=uid*10+j)).strftime('%Y-%m-%dT%H:%M:%SZ')
                c.execute('INSERT OR IGNORE INTO "like"(user_id,post_id,created_at) VALUES (?,?,?)',(uid,pid,stamp))
            for j,pid in enumerate(held):
                stamp=(datetime(2025,1,20,tzinfo=timezone.utc)+timedelta(minutes=uid*10+j)).strftime('%Y-%m-%dT%H:%M:%SZ')
                c.execute('INSERT OR IGNORE INTO "like"(user_id,post_id,created_at) VALUES (?,?,?)',(uid,pid,stamp))
    print(f'Seeded {len(USERS)} users and demo posts/likes.')
if __name__=='__main__': seed()
