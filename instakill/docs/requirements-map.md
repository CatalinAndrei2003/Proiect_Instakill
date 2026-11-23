# Requirements map (Weeks 1–5)

## Week 1 — starter foundation
- Kept the original `User` and `Post` Pydantic models in `app/domain/models.py`.
- FastAPI entry point: `app/main.py`; SQLite bootstrap: `app/db/database.py`; health route: `GET /health`.
- Tests are run with `pytest`.

## Week 2 — application boundary
- Typed application operations live in `app/services/social_service.py`.
- SQLite access lives in `app/repositories/social_repository.py`; service has no SQL or HTTP code.
- The Week 2 planned endpoint contract was replaced by the implemented contracts in `docs/api-contract.md`.

## Week 3 — semantic search
- `GET /search` validates `q` and `limit`, returns query and scored results, with deterministic score/post-id ordering.
- Encoder adapter: `app/search/encoder.py`; in-memory startup index: `app/search/index.py`; pure cosine/top-k: `app/search/retrieval.py`.
- No vector database, hosted embedding API, search framework, or sklearn nearest-neighbour implementation is used. Install the optional `semantic` extra for the pretrained SentenceTransformer; offline fallback is deterministic token hashing and should only be used for local/demo runs.

## Week 4 — feed
- `GET /feed` supports `for_you`, `chronological`, and `learned` with defaults and validation.
- `follow` and `like` tables are created by the database bootstrap; the seed script populates them.
- `rank_feed` is pure, uses heap top-k, receives `now`, and has deterministic ties. Signals and weights are documented in `docs/api-contract.md` and `README.md`.
- Candidates exclude own and previously liked posts; users with no follows see all other authors' posts.
- `tests/test_ranking.py` and `tests/test_api_feed.py` cover ranking and API behavior.

## Week 5 — evaluation
- CRUD and follow/like actions are implemented at the API edge; ranking/search remain separate.
- `scripts/evaluate.py` creates a time-split snapshot, uses the API's `FeedService` for feed strategies, computes NDCG@10, paired bootstrap intervals, activity slices, CSV/Markdown and a static dashboard.
- Popularity is only an evaluation scorer; it is not an API feed strategy.
- Evaluation dependencies are optional (`.[eval]`). Run `pytest` for tests.
- The starter archive did not include the official MovieLens seeder or `like_model.npz`; `seed_db.py` creates reproducible demo data and learned mode uses fallback weights until the course model is supplied. Do not submit the generated demo scores as official MovieLens results.
