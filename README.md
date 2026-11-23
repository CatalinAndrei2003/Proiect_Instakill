**InstaKill** is a small social-network backend developed as a multi-week Programming for AI project. It uses **Python, FastAPI, SQLite and Pydantic** and demonstrates a layered application structure, semantic post search, feed ranking, CRUD operations, and an offline feed-evaluation workflow.

> **Course-data note:** The supplied starter archive did not include the official MovieLens seeder or the trained `like_model.npz` artifact. The included seeder creates deterministic demo data so the application and evaluation pipeline can be exercised. Demo results are not official MovieLens results. Use the course dataset and trained model for formal Week 5 reporting.

## Features

- Pydantic domain models for `User` and `Post`.
- SQLite persistence with repository and application-service boundaries.
- User and post CRUD, including editing and deletion.
- Follow and like interactions.
- `GET /search` with cosine similarity and deterministic top-k retrieval.
- `GET /feed` with `for_you`, `chronological`, and `learned` strategies.
- A pure heap-based feed-ranking function with deterministic tie-breaking.
- Week 5 evaluation: time-split snapshot, NDCG@10, bootstrap confidence intervals, activity slices, CSV/Markdown reports, and a static HTML dashboard.
- Automated tests with pytest.

## Project layout

```text
instakill/
├── app/
│   ├── api/              # API package
│   ├── db/               # SQLite bootstrap and connection
│   ├── domain/            # User and Post models
│   ├── feed/              # Feed service and ranking
│   ├── repositories/       # Database access
│   ├── search/             # Encoder, index and retrieval
│   ├── services/            # Application-level coordination
│   └── main.py              # FastAPI application and routes
├── docs/
│   ├── api-contract.md
│   ├── evaluation-protocol.md
│   └── requirements-map.md
├── reports/                 # Example evaluation outputs
├── scripts/
│   ├── seed_db.py
│   └── evaluate.py
├── tests/
└── pyproject.toml
```

## Requirements

- Python 3.11 or newer
- pip
- Optional: `sentence-transformers` for pretrained semantic embeddings
- Optional: `pandas` and `matplotlib` for evaluation tooling

## Installation and run

Run these commands from the project root (`instakill/`).

### Windows PowerShell (PyCharm terminal or VS Code terminal)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
python scripts/seed_db.py
uvicorn app.main:app --reload
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
python scripts/seed_db.py
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health check: `http://127.0.0.1:8000/health`

The database is initialized by the application startup and seeder. The seeder is designed to provide repeatable demo users, posts, follows, and historical likes. Run it against a disposable database if you want to reset or regenerate demo data.

## API overview

See [`docs/api-contract.md`](docs/api-contract.md) for request and response details. The main endpoints include:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/users` | List users |
| `GET` | `/users/{user_id}` | Get a user |
| `POST` | `/users` | Create a user |
| `PUT` | `/users/{user_id}` | Rename a user |
| `DELETE` | `/users/{user_id}` | Delete a user |
| `GET` | `/posts` | List posts |
| `GET` | `/posts/{post_id}` | Get a post |
| `POST` | `/posts` | Create a post |
| `PUT` | `/posts/{post_id}` | Edit a post |
| `DELETE` | `/posts/{post_id}` | Delete a post |
| `POST` | `/users/{user_id}/follow/{author_id}` | Follow an author |
| `POST` | `/users/{user_id}/like/{post_id}` | Like a post |
| `GET` | `/search?q=...&limit=10` | Search posts |
| `GET` | `/feed?user_id=1&limit=20&strategy=for_you` | Retrieve a ranked feed |

FastAPI validation errors are returned as HTTP 422. Application-level errors use appropriate 4xx status codes, such as 404 for missing resources.

## Semantic search

The search index is built in memory when the application starts and refreshed after a post is created, edited, or deleted. The encoder attempts to use `sentence-transformers/all-MiniLM-L6-v2` when the optional dependency and model are available. If not, the project uses a deterministic token-hashing fallback; this fallback is useful for running offline but is **not** a pretrained semantic encoder.

Install the optional semantic dependency with:

```bash
pip install -e ".[semantic]"
```

The retrieval and cosine-similarity/top-k logic is implemented by the project; no vector database or external hosted embedding API is used.

## Feed strategies and ranking

`GET /feed` supports:

- **`for_you`** — ranks eligible candidate posts using freshness, affinity, and popularity.
- **`chronological`** — returns the newest eligible posts first.
- **`learned`** — uses the optional course model artifact when present; otherwise it uses a documented fallback and must not be interpreted as a trained-model result.

Candidate posts exclude the requesting user's own posts and posts the user has already liked. If the user follows authors, posts from followed authors are candidates. If the user follows nobody, the feed uses posts from other authors as the cold-start candidate set.

The default `for_you` score is:

```text
score = 0.45 * freshness + 0.40 * affinity + 0.15 * popularity
```

Where:

- `freshness = exp(-age_hours / 24)`
- `affinity = 1.0` for a followed author, `0.5` for an author whose content the user has liked before, otherwise `0.0`
- `popularity = min(1, log(1 + likes) / log(101))`

The pure `rank_feed` function uses heap-based top-k selection and deterministic post-ID tie-breaking. For `C` candidates and requested limit `k`, ranking is `O(C log k)` time and `O(k)` heap space; candidate retrieval and signal construction are `O(C)`. A useful first optimization would be to precompute popularity and author-affinity features and refresh them when likes or follows change.

## Tests

Install development dependencies and run:

```bash
pytest
```

Tests cover the health endpoint, search behavior, feed API behavior, ranking properties, and evaluation utilities. Evaluation tests use temporary fixture databases rather than modifying the working database.

## Week 5 evaluation

Install optional evaluation dependencies:

```bash
pip install -e ".[eval]"
```

Run the evaluation script:

```bash
python scripts/evaluate.py --db instakill.db --seed 42 --out reports/
```

You may specify an explicit cutoff:

```bash
python scripts/evaluate.py --db instakill.db --cutoff "2025-01-15T00:00:00Z" --seed 42 --out reports/
```

If you have the training cutoff for the course model, provide it to quantify possible overlap with the evaluation period:

```bash
python scripts/evaluate.py --db instakill.db --model-trained-through "YYYY-MM-DDTHH:MM:SSZ" --seed 42 --out reports/
```

The script generates:

- `reports/eval_results.csv` — one NDCG@10 result per qualifying user and strategy
- `reports/baseline_table.md` — strategy means, bootstrap intervals, overall and activity-slice comparisons, and run metadata
- `reports/dashboard.html` — a static dashboard with embedded charts, viewable by opening the file in a browser

Read [`docs/evaluation-protocol.md`](docs/evaluation-protocol.md) before interpreting the results. The official Week 5 submission requires the course MovieLens data and model, and the report must disclose any potential training/evaluation overlap.

## Design boundaries

- **Domain:** Pydantic `User` and `Post` models.
- **Repository:** SQLite reads and writes.
- **Application service:** coordinates domain operations and repositories.
- **Search adapter/index:** encoder access and in-memory indexed vectors.
- **Feed service/ranker:** feed orchestration and pure ranking.
- **API edge:** HTTP query parsing, validation, status codes, and response formatting.
- **Evaluation script:** offline experiment; it is not exposed as an API endpoint.
