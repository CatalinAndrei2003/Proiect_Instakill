from fastapi.testclient import TestClient
from app.main import app
from app.db.database import init_db, get_connection
from app.feed.service import FeedService
from app.repositories.social_repository import SocialRepository

def test_feed_api_on_fixture_db(tmp_path, monkeypatch):
    db=tmp_path/'api.db'; init_db(db)
    with get_connection(db) as c:
        c.execute("INSERT INTO user(username) VALUES ('reader')")
        c.execute("INSERT INTO user(username) VALUES ('author')")
        c.execute("INSERT INTO post(user_id,content,created_at) VALUES (2,'fixture post','2025-01-01T00:00:00Z')")
    monkeypatch.setattr('app.main.feed',FeedService(SocialRepository(db)))
    with TestClient(app) as client:
        response=client.get('/feed?user_id=1&limit=5&strategy=for_you')
    assert response.status_code==200
    assert response.json()['results'][0]['content']=='fixture post'
