from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, Field, field_validator
from app.db.database import init_db
from app.repositories.social_repository import SocialRepository
from app.services.social_service import SocialService
from app.search.index import SearchIndex
from app.feed.service import FeedService

repo=SocialRepository(); social=SocialService(repo); feed=FeedService(repo); search_index=SearchIndex(repo)
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(); search_index.rebuild(); yield
app=FastAPI(title='InstaKill',version='0.5.0',lifespan=lifespan)
@app.get('/health')
def health(): return {'status':'ok'}
class UserCreate(BaseModel):
    username:str=Field(min_length=1,max_length=80)
    @field_validator('username')
    @classmethod
    def username_not_blank(cls,value):
        value=value.strip()
        if not value: raise ValueError('username must not be blank')
        return value
class PostCreate(BaseModel):
    user_id:int
    content:str=Field(min_length=1,max_length=5000)
    @field_validator('content')
    @classmethod
    def content_not_blank(cls,value):
        value=value.strip()
        if not value: raise ValueError('content must not be blank')
        return value
class PostUpdate(BaseModel):
    content:str=Field(min_length=1,max_length=5000)
    @field_validator('content')
    @classmethod
    def content_not_blank(cls,value):
        value=value.strip()
        if not value: raise ValueError('content must not be blank')
        return value
@app.get('/users')
def list_users(): return [u.model_dump(mode='json') for u in social.list_users()]
@app.get('/users/{user_id}')
def get_user(user_id:int):
    u=social.get_user(user_id)
    if not u: raise HTTPException(404,'user not found')
    return u.model_dump(mode='json')
@app.post('/users',status_code=201)
def create_user(body:UserCreate):
    try:return social.register_user(body.username).model_dump(mode='json')
    except Exception as e: raise HTTPException(409,str(e))
@app.put('/users/{user_id}')
def update_user(user_id:int,body:UserCreate):
    try:
        u=social.rename_user(user_id,body.username)
        if not u: raise HTTPException(404,'user not found')
        return u.model_dump(mode='json')
    except HTTPException: raise
    except Exception as e: raise HTTPException(409,str(e))
@app.delete('/users/{user_id}',status_code=204)
def delete_user(user_id:int):
    if not social.remove_user(user_id): raise HTTPException(404,'user not found')
    return Response(status_code=204)
@app.get('/posts')
def list_posts(): return [p.model_dump(mode='json') for p in social.list_posts()]
@app.get('/posts/{post_id}')
def get_post(post_id:int):
    p=social.get_post(post_id)
    if not p: raise HTTPException(404,'post not found')
    return p.model_dump(mode='json')
@app.post('/posts',status_code=201)
def create_post(body:PostCreate):
    try:
        post=social.publish_post(body.user_id,body.content); search_index.rebuild(); return post.model_dump(mode='json')
    except LookupError as e: raise HTTPException(404,str(e))
@app.put('/posts/{post_id}')
def update_post(post_id:int,body:PostUpdate):
    p=social.edit_post(post_id,body.content)
    if not p: raise HTTPException(404,'post not found')
    search_index.rebuild(); return p.model_dump(mode='json')
@app.delete('/posts/{post_id}',status_code=204)
def delete_post(post_id:int):
    if not social.remove_post(post_id): raise HTTPException(404,'post not found')
    search_index.rebuild(); return Response(status_code=204)
@app.post('/users/{user_id}/follow/{author_id}',status_code=204)
def follow_user(user_id:int,author_id:int):
    try:social.follow_author(user_id,author_id)
    except LookupError as e: raise HTTPException(404,str(e))
    except ValueError as e: raise HTTPException(400,str(e))
    return Response(status_code=204)
@app.post('/users/{user_id}/like/{post_id}',status_code=204)
def like_post(user_id:int,post_id:int):
    try:social.like_post(user_id,post_id)
    except LookupError as e: raise HTTPException(404,str(e))
    return Response(status_code=204)
@app.get('/search')
def search(q:str=Query(...,min_length=1),limit:int=Query(10,ge=1,le=20)):
    q=q.strip()
    if not q: raise HTTPException(400,'q must be a non-empty query')
    if not search_index.posts: search_index.rebuild()
    return {'query':q,'results':search_index.search(q,limit)}
@app.get('/feed')
def get_feed(user_id:int=Query(...),limit:int=Query(20,ge=1,le=50),strategy:str=Query('for_you')):
    try:return feed.get_feed(user_id,limit,strategy)
    except LookupError as e: raise HTTPException(404,str(e))
    except ValueError as e: raise HTTPException(400,str(e))
