"""In-memory search index built at application startup."""
from app.search.encoder import TextEncoder
from app.search.retrieval import retrieve_top
class SearchIndex:
    def __init__(self, repository, encoder=None): self.repo=repository; self.encoder=encoder or TextEncoder(); self.posts=[]; self.vectors=[]
    def rebuild(self):
        self.posts=self.repo.get_search_posts()
        self.vectors=self.encoder.encode([p['content'] for p in self.posts]) if self.posts else []
    def search(self, query, limit):
        q=self.encoder.encode([query])[0]
        return retrieve_top(q,self.posts,self.vectors,limit)
