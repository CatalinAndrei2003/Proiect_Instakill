"""Encoder adapter. Uses sentence-transformers when configured; deterministic local fallback otherwise."""
import hashlib, math, re
class TextEncoder:
    def __init__(self, model_name='sentence-transformers/all-MiniLM-L6-v2', dimensions=384):
        self.model_name=model_name; self.dimensions=dimensions; self._model=None
    def _load(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model=SentenceTransformer(self.model_name)
            except Exception:
                self._model=False
        return self._model
    def encode(self, texts):
        model=self._load()
        if model:
            vectors=model.encode(texts, normalize_embeddings=True)
            return [list(map(float,v)) for v in vectors]
        # Offline, dependency-free fallback for development/tests; replace with pretrained encoder for semantic quality.
        result=[]
        for text in texts:
            v=[0.0]*self.dimensions
            tokens=re.findall(r"[\w']+",text.lower())
            for token in tokens:
                idx=int(hashlib.sha256(token.encode()).hexdigest()[:8],16)%self.dimensions
                v[idx]+=1.0
            norm=math.sqrt(sum(x*x for x in v)) or 1.0
            result.append([x/norm for x in v])
        return result
