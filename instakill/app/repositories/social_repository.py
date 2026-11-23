"""All SQLite access is isolated in this repository."""
from datetime import datetime, timezone
from app.db.database import get_connection
from app.domain.models import User, Post

class SocialRepository:
    def __init__(self, db_path=None): self.db_path = db_path
    def users(self):
        with get_connection(self.db_path) as c:
            return [User(**dict(r)) for r in c.execute('SELECT * FROM user ORDER BY id')]
    def get_user(self, user_id):
        with get_connection(self.db_path) as c:
            r=c.execute('SELECT * FROM user WHERE id=?',(user_id,)).fetchone()
            return User(**dict(r)) if r else None
    def create_user(self, username):
        with get_connection(self.db_path) as c:
            cur=c.execute('INSERT INTO user(username) VALUES (?)',(username,)); r=c.execute('SELECT * FROM user WHERE id=?',(cur.lastrowid,)).fetchone()
            return User(**dict(r))
    def update_user(self, user_id, username):
        with get_connection(self.db_path) as c:
            changed=c.execute('UPDATE user SET username=? WHERE id=?',(username,user_id)).rowcount
            r=c.execute('SELECT * FROM user WHERE id=?',(user_id,)).fetchone()
            return User(**dict(r)) if changed and r else None
    def delete_user(self, user_id):
        with get_connection(self.db_path) as c: return c.execute('DELETE FROM user WHERE id=?',(user_id,)).rowcount
    def posts(self):
        with get_connection(self.db_path) as c:
            return [Post(**dict(r)) for r in c.execute('SELECT * FROM post ORDER BY id')]
    def get_post(self, post_id):
        with get_connection(self.db_path) as c:
            r=c.execute('SELECT * FROM post WHERE id=?',(post_id,)).fetchone()
            return Post(**dict(r)) if r else None
    def create_post(self, user_id, content):
        with get_connection(self.db_path) as c:
            cur=c.execute('INSERT INTO post(user_id,content) VALUES (?,?)',(user_id,content)); r=c.execute('SELECT * FROM post WHERE id=?',(cur.lastrowid,)).fetchone()
            return Post(**dict(r))
    def update_post(self, post_id, content):
        with get_connection(self.db_path) as c:
            changed=c.execute('UPDATE post SET content=? WHERE id=?',(content,post_id)).rowcount
            r=c.execute('SELECT * FROM post WHERE id=?',(post_id,)).fetchone()
            return Post(**dict(r)) if changed and r else None
    def delete_post(self, post_id):
        with get_connection(self.db_path) as c: return c.execute('DELETE FROM post WHERE id=?',(post_id,)).rowcount
    def get_search_posts(self):
        with get_connection(self.db_path) as c:
            return [dict(r) for r in c.execute('SELECT id AS post_id,user_id,content,created_at FROM post ORDER BY id')]
    def feed_data(self, user_id):
        with get_connection(self.db_path) as c:
            follows={r[0] for r in c.execute('SELECT followed_id FROM follow WHERE follower_id=?',(user_id,))}
            liked={r[0] for r in c.execute('SELECT post_id FROM like WHERE user_id=?',(user_id,))}
            liked_authors={r[0] for r in c.execute('SELECT DISTINCT p.user_id FROM like l JOIN post p ON p.id=l.post_id WHERE l.user_id=?',(user_id,))}
            posts=[dict(r) for r in c.execute('SELECT p.id AS post_id,p.user_id,p.content,p.created_at,COUNT(l.user_id) AS likes FROM post p LEFT JOIN like l ON l.post_id=p.id GROUP BY p.id')]
            return follows,liked,liked_authors,posts
    def follow(self, follower_id, followed_id):
        with get_connection(self.db_path) as c: c.execute('INSERT OR IGNORE INTO follow(follower_id,followed_id) VALUES (?,?)',(follower_id,followed_id))
    def like(self, user_id, post_id):
        with get_connection(self.db_path) as c: c.execute('INSERT OR IGNORE INTO like(user_id,post_id) VALUES (?,?)',(user_id,post_id))
    def all_rows(self, table):
        if table not in {'user','post','follow','like'}: raise ValueError('unsupported table')
        with get_connection(self.db_path) as c: return [dict(r) for r in c.execute(f'SELECT * FROM {table}')]
