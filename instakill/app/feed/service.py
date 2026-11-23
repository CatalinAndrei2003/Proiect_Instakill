"""Feed orchestration shared by API and evaluation."""
from datetime import datetime, timezone
from app.repositories.social_repository import SocialRepository
from app.feed.ranking import build_signals, rank_feed
DEFAULT_WEIGHTS={'freshness':0.45,'affinity':0.40,'popularity':0.15}

class FeedService:
    def __init__(self, repository=None): self.repo=repository or SocialRepository()
    def get_feed(self, user_id: int, limit: int=20, strategy: str='for_you', now: datetime|None=None):
        user=self.repo.get_user(user_id)
        if user is None: raise LookupError('user not found')
        if not 1<=limit<=50: raise ValueError('limit must be between 1 and 50')
        if strategy not in {'for_you','chronological','learned'}: raise ValueError('unknown strategy')
        follows,liked,liked_authors,all_posts=self.repo.feed_data(user_id)
        candidates=[p for p in all_posts if int(p['user_id'])!=user_id and int(p['post_id']) not in liked]
        # Followed authors form the normal candidate set. Cold-start users see all public posts.
        if follows: candidates=[p for p in candidates if int(p['user_id']) in follows]
        if strategy=='chronological':
            result=sorted(candidates,key=lambda p:(p['created_at'], -int(p['post_id'])),reverse=True)
            # deterministic tie: ascending id for equal timestamps
            result=sorted(result,key=lambda p:(p['created_at'], -int(p['post_id'])),reverse=True)
            # Explicit stable key: newest first, then smallest post_id.
            result=sorted(result,key=lambda p:(-int(p['post_id'])))
            result=sorted(result,key=lambda p:p['created_at'],reverse=True)
            result=[{k:p[k] for k in ('post_id','user_id','content','created_at')} for p in result[:limit]]
        else:
            current=now or datetime.now(timezone.utc)
            signals=build_signals(candidates,follows,liked_authors,current)
            weights=DEFAULT_WEIGHTS
            if strategy=='learned':
                # Optional lab model weights; without the lab asset, use documented fixed fallback.
                try:
                    import numpy as np
                    data=np.load('like_model.npz')
                    raw=data['weights'].tolist()
                    weights={'freshness':float(raw[0]),'affinity':float(raw[1]),'popularity':float(raw[2])}
                except Exception:
                    weights={'freshness':0.30,'affinity':0.55,'popularity':0.15}
            result=rank_feed(candidates,signals,current,weights,limit)
            result=[{k:p[k] for k in ('post_id','user_id','content','created_at','score')} for p in result]
        return {'user_id':user_id,'strategy':strategy,'results':result}
