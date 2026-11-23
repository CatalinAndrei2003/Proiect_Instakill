# Week 5 evaluation protocol

**Question.** Measure whether chronological, popularity, for_you and learned place later-liked posts in the top ten, across users and activity groups.

**Cut-off and snapshot.** Default cutoff is the timestamp at which 80% of likes occurred; an ISO cutoff can override it. Copy the database to a temporary SQLite file and remove likes, posts and follows at or after T. If follows are derived from likes, derive them only from snapshot likes.

**Users.** Qualify users with at least three likes before T and at least one later like of a post present in the snapshot.

**Candidates.** Call the same FeedService as the API for each strategy at `now=T`, limit 10. Own posts and previously liked posts are excluded.

**Relevance.** A snapshot post is relevant when the user liked it after T and it existed in the snapshot.

**Metric.** NDCG@10 uses binary relevance and logarithmic discount, normalized by ideal DCG; one value per user and strategy.

**Intervals.** A fixed-seed paired bootstrap over users estimates 95% percentile intervals for strategy means and learned minus strongest baseline. Wins/losses require the difference interval to exclude zero; otherwise verdict is unclear.

**Slices.** Activity groups before T: new (<10 likes), casual (10–49), regular (50–199), power (200+).

**Limitations.** The provided starter archive lacks the course MovieLens seeder and `like_model.npz`; learned therefore uses fallback weights until the lab asset is added, and no official model score can be claimed. MovieLens ratings are older than social posts; results may not generalize to feeds dominated by posts from the last few days. These metrics are not comparable to the lab's one-hidden-like among 99 random items because this protocol ranks the whole candidate set and counts every later like.
