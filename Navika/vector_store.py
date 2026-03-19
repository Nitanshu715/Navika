import faiss
import numpy as np

class VectorStore:
    def __init__(self, dim=384):
        self.index = faiss.IndexFlatL2(dim)
        self.metadata = []

    def add(self, embedding, meta):
        vec = np.array([embedding]).astype("float32")
        self.index.add(vec)
        self.metadata.append(meta)

    def search(self, embedding, top_k=5):
        if self.index.ntotal == 0:
            return []

        vec = np.array([embedding]).astype("float32")
        distances, indices = self.index.search(vec, top_k)

        results = []
        for idx in indices[0]:
            if idx < len(self.metadata):
                results.append(self.metadata[idx])
        return results