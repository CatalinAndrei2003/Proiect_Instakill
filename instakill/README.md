# InstaKill

FastAPI + SQLite mini social network with search, feed strategies, CRUD and evaluation scaffold.

## Run (PyCharm or VS Code)
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
python scripts/seed_db.py
uvicorn app.main:app --reload
pytest
```
Visit `http://127.0.0.1:8000/docs` for Swagger UI.

## Search index
`SearchIndex.rebuild()` runs at startup and after post create/delete. It encodes current posts into an in-memory vector list. A new post refreshes the index after its database transaction. `TextEncoder` uses `sentence-transformers/all-MiniLM-L6-v2` if available; offline fallback is deterministic token hashing, not semantic pretrained embeddings. Install `.[semantic]` for the pretrained encoder.

## Feed
Candidates are followed authors' posts; cold-start users (no follows) see all other authors. Own posts and previously liked posts are excluded. Formula: `0.45*freshness + 0.40*affinity + 0.15*popularity`; freshness=`exp(-age_hours/24)`, affinity=1 for followed authors and 0.5 for authors previously liked, popularity=`min(1, log(1+likes)/log(101))`. `rank_feed` is pure and heap-based. Learned mode reads optional `like_model.npz`; absent it uses a transparent fallback, not trained weights.

For C candidates and limit k, ranking is O(C log k) time and O(k) heap space; retrieval and signal construction are O(C). Precompute popularity and author-affinity features first, invalidating on likes/follows.

## Evaluation
`python scripts/evaluate.py [--db instakill.db] [--cutoff ISO-date] [--seed 42] [--out reports/]`. Install with `pip install -e ".[eval]"`. The starter archive did not include the course MovieLens seeder, `like_model.npz`, or its training cut-off; this included seeder is deterministic demo data for exercising the pipeline, not official MovieLens results. Supply the lab cutoff with `--model-trained-through ISO-date` to quantify potential future leakage. Replace it with the course data before submitting formal Week 5 metrics.
