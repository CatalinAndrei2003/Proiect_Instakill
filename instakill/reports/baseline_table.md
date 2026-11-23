# Baseline comparison

**Demo seed data only — not official MovieLens results; learned uses fallback weights unless the lab model is supplied.**

- Cut-off: `2025-01-20T00:22:00Z`
- Seed: `42`
- Users: `14`
- Evaluation likes on snapshot posts: `40`
- Evaluation likes within model training period: `unknown (provide --model-trained-through)`
- DB SHA256: `a5c5cc9fea26ec87b5377697c32674af0e98bd444a31b7efb9edd115f0988a85`
- Git commit: `unavailable`

| Strategy | Mean NDCG@10 | 95% bootstrap interval | Users |
|---|---:|---:|---:|
| chronological | 1.0000 | [1.0000, 1.0000] | 14 |
| popularity | 0.0000 | [0.0000, 0.0000] | 14 |
| for_you | 1.0000 | [1.0000, 1.0000] | 14 |
| learned | 1.0000 | [1.0000, 1.0000] | 14 |

Learned minus best baseline (chronological): 0.0000, 95% CI [0.0000, 0.0000] — **unclear**

## Activity slices

- new: no qualifying users
- casual (n=14): learned − chronological = 0.0000, 95% CI [0.0000, 0.0000] — unclear
- regular: no qualifying users
- power: no qualifying users
