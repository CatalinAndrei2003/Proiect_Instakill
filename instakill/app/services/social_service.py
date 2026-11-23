"""Typed application operations; no HTTP or SQL code belongs here."""
from app.domain.models import User, Post
from app.repositories.social_repository import SocialRepository

class SocialService:
    def __init__(self, repository: SocialRepository | None = None): self.repo=repository or SocialRepository()
    def list_users(self) -> list[User]: return self.repo.users()
    def get_user(self, user_id: int) -> User | None: return self.repo.get_user(user_id)
    def register_user(self, username: str) -> User: return self.repo.create_user(username.strip())
    def rename_user(self, user_id: int, username: str) -> User | None: return self.repo.update_user(user_id,username.strip())
    def remove_user(self, user_id: int) -> bool: return bool(self.repo.delete_user(user_id))
    def list_posts(self) -> list[Post]: return self.repo.posts()
    def get_post(self, post_id: int) -> Post | None: return self.repo.get_post(post_id)
    def publish_post(self, user_id: int, content: str) -> Post:
        if not self.repo.get_user(user_id): raise LookupError('user not found')
        return self.repo.create_post(user_id,content.strip())
    def edit_post(self, post_id: int, content: str) -> Post | None: return self.repo.update_post(post_id,content.strip())
    def remove_post(self, post_id: int) -> bool: return bool(self.repo.delete_post(post_id))
    def follow_author(self, follower_id: int, author_id: int) -> None:
        if not self.repo.get_user(follower_id) or not self.repo.get_user(author_id): raise LookupError('user not found')
        if follower_id==author_id: raise ValueError('cannot follow yourself')
        self.repo.follow(follower_id,author_id)
    def like_post(self, user_id: int, post_id: int) -> None:
        if not self.repo.get_user(user_id) or not self.repo.get_post(post_id): raise LookupError('user or post not found')
        self.repo.like(user_id,post_id)
