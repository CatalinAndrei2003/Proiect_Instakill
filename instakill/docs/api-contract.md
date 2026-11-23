# InstaKill API contract

All endpoints return JSON unless noted. FastAPI validation errors use HTTP 422; application errors use the status described below.

## `GET /health`
No parameters. `200`: `{"status":"ok"}`.

## `GET /search?q=<non-empty>&limit=<1..20>`
`q` is required and non-blank; `limit` defaults to 10. `200`: `{ "query": "...", "results": [{"post_id":1,"user_id":1,"content":"...","created_at":"...","score":0.8}] }`. Scores are cosine similarity; descending score, then ascending `post_id`. Blank/missing query or invalid limit returns a client validation error. Search index is built at startup and rebuilt after post create/delete.

## `GET /feed?user_id=<int>&limit=<1..50>&strategy=for_you|chronological|learned`
`user_id` required, `limit` defaults to 20, `strategy` defaults to `for_you`. `200`: `{ "user_id": 1, "strategy":"for_you", "results":[{"post_id":2,"user_id":3,"content":"...","created_at":"...","score":0.4}] }`. `score` is returned for `for_you` and `learned`. Unknown user: `404`; invalid limit/strategy: `400` or FastAPI `422`.

Candidates are posts by followed authors, excluding own posts and posts already liked. If the user follows nobody, all other users' posts are candidates. Signals: freshness `exp(-age_hours/24)`, affinity (1.0 followed author, 0.5 author previously liked, otherwise 0), popularity `min(1, log(1+likes)/log(101))`. Default `for_you` weights: freshness 0.45, affinity 0.40, popularity 0.15. Heap top-k ties use ascending post ID. `chronological` is newest first, then ascending post ID. `learned` loads optional `like_model.npz`; absent the course model it uses fallback weights, not a trained result.

## CRUD / interactions
- `GET /users`, `GET /users/{id}`, `POST /users` (`{"username":"..."}`; 201), `PUT /users/{id}` (rename), `DELETE /users/{id}` (204; 404 if missing).
- `GET /posts`, `GET /posts/{id}`, `POST /posts` (`{"user_id":1,"content":"..."}`; 201), `PUT /posts/{id}` (edit content), `DELETE /posts/{id}` (204; 404 if missing).
- `POST /users/{user_id}/follow/{author_id}` (204; self-follow is 400).
- `POST /users/{user_id}/like/{post_id}` (204).
