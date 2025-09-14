# rag_index.py
from __future__ import annotations
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

try:
    import faiss  # type: ignore
    _FAISS_OK = True
except Exception:
    _FAISS_OK = False

from sentence_transformers import SentenceTransformer

def _l2_normalize(x: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(x, axis=1, keepdims=True) + 1e-12
    return x / norms

class VectorIndexer:
    """
    Tiny vector store with FAISS (if present) or numpy fallback.
    Uses cosine similarity (via inner product on normalized vectors).
    """
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        index_dir: str = ".rag_cache",
        index_name: str = "kb_index",
        use_faiss: Optional[bool] = None,
    ):
        self.model = SentenceTransformer(model_name)
        self.index_dir = index_dir
        self.index_name = index_name
        self.use_faiss = _FAISS_OK if use_faiss is None else use_faiss
        os.makedirs(self.index_dir, exist_ok=True)

        self._faiss_index = None
        self._embeddings = None  # numpy fallback
        self._metadata: List[Dict[str, Any]] = []
        self._dim: Optional[int] = None

    # ---------- paths
    @property
    def _meta_path(self) -> str:
        return os.path.join(self.index_dir, f"{self.index_name}.meta.json")

    @property
    def _faiss_path(self) -> str:
        return os.path.join(self.index_dir, f"{self.index_name}.faiss")

    @property
    def _npy_path(self) -> str:
        return os.path.join(self.index_dir, f"{self.index_name}.npy")

    # ---------- build / save / load
    def build(self, texts: List[str], metadata: List[Dict[str, Any]]) -> None:
        assert len(texts) == len(metadata), "texts and metadata length mismatch"
        emb = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        emb = _l2_normalize(emb)
        self._dim = emb.shape[1]
        self._metadata = metadata

        if self.use_faiss:
            index = faiss.IndexFlatIP(self._dim)  # inner product on normalized vectors == cosine
            index.add(emb.astype(np.float32))
            self._faiss_index = index
            # persist
            faiss.write_index(index, self._faiss_path)
        else:
            self._embeddings = emb
            np.save(self._npy_path, emb)

        with open(self._meta_path, "w", encoding="utf-8") as f:
            json.dump({"metadata": self._metadata, "dim": self._dim}, f, ensure_ascii=False)

    def load(self) -> bool:
        if not os.path.exists(self._meta_path):
            return False
        with open(self._meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        self._metadata = meta["metadata"]
        self._dim = meta["dim"]

        if self.use_faiss and os.path.exists(self._faiss_path):
            self._faiss_index = faiss.read_index(self._faiss_path)
            return True
        if not self.use_faiss and os.path.exists(self._npy_path):
            self._embeddings = np.load(self._npy_path)
            return True
        return False

    # ---------- search
    def encode_query(self, text: str) -> np.ndarray:
        q = self.model.encode([text], convert_to_numpy=True, show_progress_bar=False)
        q = _l2_normalize(q).astype(np.float32)
        return q

    def search(self, query: str, top_k: int = 12) -> List[Tuple[int, float]]:
        q = self.encode_query(query)
        if self.use_faiss and self._faiss_index is not None:
            scores, idxs = self._faiss_index.search(q, top_k)
            # scores shape (1, k); idxs shape (1, k)
            return [(int(i), float(s)) for i, s in zip(idxs[0], scores[0]) if i != -1]
        elif self._embeddings is not None:
            sims = (self._embeddings @ q[0].reshape(-1, 1)).ravel()  # cosine on normalized
            top_idx = np.argsort(-sims)[:top_k]
            return [(int(i), float(sims[i])) for i in top_idx]
        else:
            raise RuntimeError("Index not built or loaded.")

    def get_metadata(self, idx: int) -> Dict[str, Any]:
        return self._metadata[idx]
