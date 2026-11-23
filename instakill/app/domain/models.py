"""Domain models retained from the Week 1 starter."""
from datetime import datetime
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int | None = None
    username: str = Field(min_length=1, max_length=80)
    created_at: datetime | None = None

class Post(BaseModel):
    id: int | None = None
    user_id: int
    content: str = Field(min_length=1, max_length=5000)
    created_at: datetime | None = None
